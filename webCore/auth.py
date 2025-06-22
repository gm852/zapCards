from functools import wraps

import jwt, sanic, random, hashlib, bcrypt,time

import sanic.response

def check_token(request):
	""" This function is designed to check the validity of a jwt token."""
	# check if required cookie exists
	if request.cookies.get("token") == None: return {"status": False}
	
	# test jwt token to validate that it can be decoded with the secret_session_token stored in the conf
	try:
		jwtTokenObj = jwt.decode(
			request.cookies.get("token"),
			request.ctx.configObj.secret_session_token,
			algorithms=["HS256"]
		)

		# get the expiration time from the config
		max_duration = int(request.ctx.configObj.jwt_expire_time)
				
		# Check if the token has expired - doing this bc sanics expire varible on init seems to not work
		if "iat" in jwtTokenObj:
			issued_at = jwtTokenObj["iat"] 
			current_time = time.time()  # Current time as a unix timestamp
			if current_time - issued_at > max_duration:
				return {"status": False, "message": "Token Expired"}
		else:
			print("Token missing 'iat' claim.")
			return {"status": False}
        
		return {"status": True, "jwtTokenObj": jwtTokenObj}
	except jwt.exceptions.InvalidTokenError:
		print("Invalid Token")
		return {"status": False}

def protected(wrapped):
	""" This decorator is designed to protect a route from unauthorized access.
		Should the user not be authorized, then they will be redirected to the /login page.
  	"""
	def decorator(f):
		@wraps(f)
		async def decorated_function(request, *args, **kwargs):

			authCheck = check_token(request) # check token for validity
			if authCheck["status"] == True:
				request.ctx.authSessionObj = authCheck["jwtTokenObj"] # pass along decoded jwt contents in the "authSessionObj" context variable

				response = await f(request, *args, **kwargs)

				return response
			else: 
				# see if auth is required
				if not request.ctx.configObj.require_auth:
					return await f(request, *args, **kwargs)
				
				res = sanic.response.redirect("/login") # redirect to /login due to unsuccessful decode / missing session cookie
				return res
			
		return decorated_function

	return decorator(wrapped)


def multi_protected(wrapped):
	""" This decorator is designed to be able to check a token if it exists and is valid, and set
		temp variables in the request object for the route to use. If the token is invalid, it will
		do nothing as the route will be unprotected.

		simply just to see if the user requesting is verified or not.
  	"""
	def decorator(f):
		@wraps(f)
		async def decorated_function(request, *args, **kwargs):
			authCheck = check_token(request) # check token for validity
			if authCheck["status"] == True:
				request.ctx.authSessionObj = authCheck["jwtTokenObj"] # pass along decoded jwt contents in the "authSessionObj" context variable
				response = await f(request, *args, **kwargs)
				return response
			else: 
				# see if auth is required
				if request.ctx.configObj.require_auth:
					return sanic.response.redirect("/login")
				
				request.ctx.authSessionObj = False
				return await f(request, *args, **kwargs)

		return decorated_function

	return decorator(wrapped)



async def verification(requestObj: sanic.Request, authUsername: str, authPasswd: str):

	# extract user record from database
	userRecordObj = await requestObj.ctx.databaseObj.getUser(authUsername)
	
	# check if user exists in the database
	if userRecordObj["status"]:
		# make sure user-submitted passwd and stored database passwd match up
		if bcrypt.checkpw(authPasswd.encode('utf-8'), userRecordObj["data"].password.encode('utf-8')):
			authSessionToken = hashlib.sha256(str(random.getrandbits(128)).encode('utf-8')).hexdigest()
			
			# generate jwt token
			authToken = jwt.encode({
				"authUser": authUsername,
				"authTraveler": userRecordObj["data"].internalID,
				"sessionToken": authSessionToken,
				"role": userRecordObj["data"].role,
				"iat": time.time()
			}, requestObj.ctx.configObj.secret_session_token)

			return {"status": True, "message": "AUTH_SUCCESS", "token": authToken}
		else: return {"status": False, "message": "INVALID_CREDENTIALS"}
	else: return {"status": False, "message": "INVALID_CREDENTIALS"}



