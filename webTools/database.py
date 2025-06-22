from webCore.models import deckModel, userModel
from sqlalchemy import select, func, and_, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
import json, bcrypt,random,string, hashlib
from datetime import datetime, timedelta

from .aiApi import OllamaModels, chatGPT


class Database:
    def __init__(self, configObj, async_session):
        self.configObj = configObj
        self.async_session = async_session
        self.ollamaObj = OllamaModels(config=configObj)
        self.chatgptObj = chatGPT(config=configObj)


    def _generate_id(self, count: int = 32):
        return ''.join(random.choices(string.ascii_letters + string.digits + r"!$%&*+-.:;?@_~", k=count))

    def _normalize_card(self, card: dict) -> str:
        return json.dumps(card, sort_keys=True)

    def _hash_card(self, card: dict) -> str:
        normalized = self._normalize_card(card)
        return hashlib.sha256(normalized.encode()).hexdigest()



    async def randomizeSecretSessionToken(self):
        # makes a new random secret session token for jwt tokens
        self.configObj.set("general", "secret_session_token", self._generate_id(32))
        self.configObj.save()
        print(f"[ DEBUG ] - Session Token was reset ")
        return True


    def generate_internal_user(self, username, password, roleType):
        return userModel.User(
            internalID=self._generate_id(32),
            username=username,
            password=bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            decksJson={},
            role=roleType,
            created=datetime.now(),
            deleted=False,
        )


    async def addNewUser(self, username="admin", password="ZapCardsAdmin!", roleType="user"):
        if self.configObj.is_async:
            async with self.async_session() as session:
                async with session.begin():
                    if self.configObj.erase_database_on_reset and self.configObj.reset_default_user:
                        await session.execute(userModel.User.__table__.delete())
                        await session.execute(deckModel.Deck.__table__.delete())

                    newUser = self.generate_internal_user(username, password, roleType)
                    session.add(newUser)

                return {"status": True, "data": newUser}
        else:
            with self.async_session() as session:
                if self.configObj.erase_database_on_reset and self.configObj.reset_default_user:
                    session.execute(userModel.User.__table__.delete())
                    session.execute(deckModel.Deck.__table__.delete())

                newUser = self.generate_internal_user(username, password, roleType)
                session.add(newUser)
                session.commit()
                return {"status": True, "data": newUser}


    async def deleteUser(self, identifier: str):
        if self.configObj.is_async:
            async with self.async_session() as session:
                async with session.begin():
                    query = select(userModel.User).filter(
                        or_(
                            userModel.User.username == identifier,
                            userModel.User.internalID == identifier
                        )
                    )
                    result = await session.execute(query)
                    user = result.scalar()

                    if not user:
                        return {"status": False, "message": "User not found."}

                    await session.delete(user)
                    return {"status": True, "message": "User deleted successfully.", "username": user.username}
        else:
            with self.async_session() as session:
                query = select(userModel.User).filter(
                    or_(
                        userModel.User.username == identifier,
                        userModel.User.internalID == identifier
                    )
                )
                result = session.execute(query)
                user = result.scalar()

                if not user:
                    return {"status": False, "message": "User not found."}

                session.delete(user)
                session.commit()
                return {"status": True, "message": "User deleted successfully.", "username": user.username}


    async def attemptUserLogin(self, request, username: str, password: str):
        if self.configObj.is_async:
            async with self.async_session() as session:
                async with session.begin():
                    result = await session.execute(
                        select(userModel.User).filter(userModel.User.username == username)
                    )
                    user_record = result.scalar()
        else:
            with self.async_session() as session:
                result = session.execute(
                    select(userModel.User).filter(userModel.User.username == username)
                )
                user_record = result.scalar()

        if not user_record:
            return {"status": False, "message": "User does not exist."}

        # paswd check
        if bcrypt.checkpw(password.encode('utf-8'), user_record.password.encode('utf-8')):
            if self.configObj.is_async:
                verifiyResults = await request.ctx.authObj.verification(request, username, password)
            else:
                verifiyResults = await request.ctx.authObj.verification(request, username, password)

            return {"status": True, "data": verifiyResults}
        else:
            return {"status": False, "message": "Invalid password."}
        

    async def getUser(self, username: str):
        if self.configObj.is_async:
            async with self.async_session() as session:
                async with session.begin():
                    query = select(userModel.User).filter(
                        or_(
                            userModel.User.username == username,
                            userModel.User.internalID == username
                        )
                    )
                    result = await session.execute(query)
                    user = result.scalar()
        else:
            with self.async_session() as session:
                query = select(userModel.User).filter(
                    or_(
                        userModel.User.username == username,
                        userModel.User.internalID == username
                    )
                )
                result = session.execute(query)
                user = result.scalar()

        if user:
            return {"status": True, "data": user}
        else:
            return {"status": False}
        

    async def getAllUsers(self, count=25):
        if self.configObj.is_async:
            async with self.async_session() as session:
                async with session.begin():
                    query = select(userModel.User).limit(count)
                    result = await session.execute(query)
                    users = result.scalars().all()
        else:
            with self.async_session() as session:
                query = select(userModel.User).limit(count)
                result = session.execute(query)
                users = result.scalars().all()

        if users:
            user_list = []
            for user in users:
                user_dict = {
                    "internalID": user.internalID,
                    "username": user.username,
                    "email": getattr(user, "email", None),
                    "created": getattr(user, "created", None),
                    "role": getattr(user, "role", "user"),
                }
                user_list.append(user_dict)
            return {"status": True, "users": user_list}
        else:
            return {"status": False, "message": "No users found."}



    async def addDeck(self, userID: str, deckJson: dict):
        """ 
        This is a long and gross function i know. this handles authed users cards being added 
        with a async/non async db and with checking if its a update or a new one
        """
        deck_hash = self._hash_card(deckJson)
        deck_id = deckJson.get("deckID")
        is_update = False
        
        # check if this is an update or new deck
        if deck_id:
            is_update = True
        else:
            deck_id = self._generate_id(64)
            deckJson["deckID"] = deck_id
            is_update = False
        

        if self.configObj.is_async:
            async with self.async_session() as session:
                async with session.begin():
                    # check user exists
                    query = select(userModel.User).where(userModel.User.internalID == userID)
                    result = await session.execute(query)
                    userRecord = result.scalar()

                    if not userRecord:
                        return {"status": False, "message": "User not found."}

                    if is_update:
                        existing_deck_query = select(deckModel.Deck).where(
                            deckModel.Deck.deckID == deck_id,
                            deckModel.Deck.ownerID == userID,
                            deckModel.Deck.deleted == False
                        )
                        existing_deck_result = await session.execute(existing_deck_query)
                        existing_deck = existing_deck_result.scalar()
                        
                        if not existing_deck:
                            return {"status": False, "message": "Deck not found or you don't have permission to update it."}
                        
                        # check if content actually changed
                        if existing_deck.deckHash == deck_hash:
                            return {"status": False, "message": "No changes detected."}
                        
                        # update existing deck
                        existing_deck.deckJson = deckJson
                        existing_deck.deckHash = deck_hash
                        existing_deck.modified = datetime.now().isoformat()  # add modified timestamp if you have this field
                        
                        await session.commit()
                        return {"status": True, "message": f"Deck '{deckJson.get('name', 'Untitled')}' updated successfully.", "deckID": deck_id}
                    
                    else:
                        # check for duplicate card hash (only for new decks)
                        dup_query = select(deckModel.Deck).where(
                            deckModel.Deck.deckHash == deck_hash,
                            deckModel.Deck.ownerID == userID,
                            deckModel.Deck.deleted == False
                        )
                        dup_result = await session.execute(dup_query)
                        if dup_result.scalar():
                            return {"status": False, "message": "A deck with identical content already exists."}

                        # insert new deck
                        new_deck = deckModel.Deck(
                            deckID=deck_id,
                            ownerID=userID,
                            created=datetime.now().isoformat(),
                            deleted=False,
                            deckJson=deckJson,
                            deckHash=deck_hash
                        )
                        session.add(new_deck)

                        # update users deck list
                        existing_decks = userRecord.decksJson or []
                        if not isinstance(existing_decks, list):
                            existing_decks = []
                        
                        # only add if not already in the list
                        if deck_id not in existing_decks:
                            existing_decks.append(deck_id)
                            userRecord.decksJson = existing_decks

                        await session.commit()
                        return {"status": True, "message": f"Deck '{deckJson.get('name', 'Untitled')}' created successfully.", "deckID": deck_id}

        else:
            with self.async_session() as session:
                # check user exists
                query = select(userModel.User).where(userModel.User.internalID == userID)
                result = session.execute(query)
                userRecord = result.scalar()

                if not userRecord:
                    return {"status": False, "message": "User not found."}

                if is_update:
                    # handle update case
                    existing_deck_query = select(deckModel.Deck).where(
                        deckModel.Deck.deckID == deck_id,
                        deckModel.Deck.ownerID == userID,
                        deckModel.Deck.deleted == False
                    )
                    existing_deck_result = session.execute(existing_deck_query)
                    existing_deck = existing_deck_result.scalar()
                    
                    if not existing_deck:
                        return {"status": False, "message": "Deck not found or you don't have permission to update it."}
                    
                    # check if content actually changed
                    if existing_deck.deckHash == deck_hash:
                        return {"status": False, "message": "No changes detected."}
                    
                    # update existing deck
                    existing_deck.deckJson = deckJson
                    existing_deck.deckHash = deck_hash
                    existing_deck.modified = datetime.now().isoformat()  # Add modified timestamp if you have this field
                    
                    session.commit()
                    return {"status": True, "message": f"Deck '{deckJson.get('name', 'Untitled')}' updated successfully.", "deckID": deck_id}
                
                else:
                    # check for duplicate card hash
                    dup_query = select(deckModel.Deck).where(
                        deckModel.Deck.deckHash == deck_hash,
                        deckModel.Deck.ownerID == userID,
                        deckModel.Deck.deleted == False
                    )
                    dup_result = session.execute(dup_query)
                    if dup_result.scalar():
                        return {"status": False, "message": "A deck with identical content already exists."}

                    # insert new deck
                    new_deck = deckModel.Deck(
                        deckID=deck_id,
                        ownerID=userID,
                        created=datetime.now().isoformat(),
                        deleted=False,
                        deckJson=deckJson,
                        deckHash=deck_hash
                    )
                    session.add(new_deck)

                    # update users deck list
                    existing_decks = userRecord.decksJson or []
                    if not isinstance(existing_decks, list):
                        existing_decks = []
                    
                    if deck_id not in existing_decks:
                        existing_decks.append(deck_id)
                        userRecord.decksJson = existing_decks

                    session.commit()
                    return {"status": True, "message": f"Deck '{deckJson.get('name', 'Untitled')}' created successfully.", "deckID": deck_id}
            

    async def getDecksByUserID(self, userID: str):
        if self.configObj.is_async:
            async with self.async_session() as session:
                async with session.begin():
                    # check if user exists
                    query = select(userModel.User).where(userModel.User.internalID == userID)
                    result = await session.execute(query)
                    userRecord = result.scalar()

                    if not userRecord:
                        return {"status": False, "message": "User not found."}

                    # fetch all decks for user
                    deck_query = select(deckModel.Deck).where(
                        deckModel.Deck.ownerID == userID,
                        deckModel.Deck.deleted == False
                    )
                    deck_result = await session.execute(deck_query)
                    decks = deck_result.scalars().all()

                    decks_json = [
                        {**deck.deckJson, "deckID": deck.deckID}
                        for deck in decks
                    ]

                    return {"status": True, "decks": decks_json}
        else:
            with self.async_session() as session:
                # check if user exists
                query = select(userModel.User).where(userModel.User.internalID == userID)
                result = session.execute(query)
                userRecord = result.scalar()

                if not userRecord:
                    return {"status": False, "message": "User not found."}

                deck_query = select(deckModel.Deck).where(
                    deckModel.Deck.ownerID == userID,
                    deckModel.Deck.deleted == False
                )
                deck_result = session.execute(deck_query)
                decks = deck_result.scalars().all()

                decks_json = [
                    {**deck.deckJson, "deckID": deck.deckID}
                    for deck in decks
                ]
                
                return {"status": True, "decks": decks_json}


        
    async def delDeck(self, deckId: str, isTemp: bool):
        if self.configObj.is_async:
            async with self.async_session() as session:
                async with session.begin():
                    model = deckModel.Tempdeck if isTemp else deckModel.Deck

                    query = select(model).where(model.deckID == deckId)
                    result = await session.execute(query)
                    card = result.scalar()

                    if not card:
                        return {"status": False, "message": "Card not found."}

                    card.deleted = True
                    await session.commit()

                    return {"status": True, "message": "Card deleted."}
        else:
            with self.async_session() as session:
                model = deckModel.Tempdeck if isTemp else deckModel.Deck

                query = select(model).where(model.deckID == deckId)
                result = session.execute(query)
                card = result.scalar()

                if not card:
                    return {"status": False, "message": "Card not found."}

                card.deleted = True
                session.commit()

                return {"status": True, "message": "Card deleted."}




    async def getModels(self):
        if self.configObj.model_type == "ollama":
            res = self.ollamaObj.list_local_models()
            
            if type(res) == list:
                return res
            else:
                return {"status": False, "message": "Ollama not found."}
        elif self.configObj.model_type == "openai":
            pass


    async def getTempDecksByClientID(self, clientID: str):
        if self.configObj.is_async:
            async with self.async_session() as session:
                async with session.begin():
                    # if id exists
                    query = select(deckModel.Tempdeck).where(
                        deckModel.Tempdeck.ownerID == clientID,
                        deckModel.Tempdeck.deleted == False
                        )
                    result = await session.execute(query)
                    decksRecord = result.scalars().all()

                    if not decksRecord:
                        return {"status": False, "message": "Deck not found."}

                    decks_json = [
                        {**decks.deckJson, "deckID": decks.deckID}
                        for decks in decksRecord
                    ]

                    return {"status": True, "decks": decks_json}
        else:
            with self.async_session() as session:
                query = select(deckModel.Tempdeck).where(
                    deckModel.Tempdeck.ownerID == clientID,
                    deckModel.Tempdeck.deleted == False
                )
                result = session.execute(query)
                decksRecord = result.scalars().all()

                if not decksRecord:
                    return {"status": False, "message": "Deck not found."}

                decks_json = [
                    {**decks.deckJson, "deckID": decks.deckID}
                    for decks in decksRecord
                ]

                return {"status": True, "decks": decks_json}
            
    async def addTempDeck(self, clientID: str, deckJson: dict):
        """ 
        This is also a long and gross function i know. but this handles non-authed users cards being added 
        with a async/non async db along with checking if its a update or a new one
        """
        deck_hash = self._hash_card(deckJson)
        deck_id = deckJson.get("deckID")
        is_update = False

        if deck_id:
            is_update = True
        else:
            deck_id = self._generate_id(64)
            deckJson["deckID"] = deck_id

        if self.configObj.is_async:
            async with self.async_session() as session:
                async with session.begin():
                    if is_update:
                        query = select(deckModel.Tempdeck).where(
                            deckModel.Tempdeck.deckID == deck_id,
                            deckModel.Tempdeck.ownerID == clientID,
                            deckModel.Tempdeck.deleted == False
                        )
                        result = await session.execute(query)
                        existing_deck = result.scalar()

                        if not existing_deck:
                            return {"status": False, "message": "Deck not found or no permission."}

                        if existing_deck.deckHash == deck_hash:
                            return {"status": False, "message": "No changes detected."}

                        existing_deck.deckJson = deckJson
                        existing_deck.deckHash = deck_hash
                        existing_deck.modified = datetime.now().isoformat()

                        await session.commit()
                        return {"status": True, "message": f"Deck '{deckJson.get('name', 'Untitled')}' updated.", "deckID": deck_id}

                    else:
                        dup_query = select(deckModel.Tempdeck).where(
                            deckModel.Tempdeck.deckID == deck_id,
                            deckModel.Tempdeck.ownerID == clientID,
                            deckModel.Tempdeck.deleted == False
                        )
                        dup_result = await session.execute(dup_query)
                        if dup_result.scalar():
                            return {"status": False, "message": "Duplicate deck already exists."}

                        new_deck = deckModel.Tempdeck(
                            deckID=deck_id,
                            ownerID=clientID,
                            created=datetime.now().isoformat(),
                            deleted=False,
                            deckJson=deckJson,
                            deckHash=deck_hash
                        )
                        session.add(new_deck)

                        await session.commit()
                        return {"status": True, "message": f"Deck '{deckJson.get('name', 'Untitled')}' created.", "deckID": deck_id}

        else:
            with self.async_session() as session:
                if is_update:
                    query = select(deckModel.Tempdeck).where(
                        deckModel.Tempdeck.deckID == deck_id,
                        deckModel.Tempdeck.ownerID == clientID,
                        deckModel.Tempdeck.deleted == False
                    )
                    result = session.execute(query)
                    existing_deck = result.scalar()

                    if not existing_deck:
                        return {"status": False, "message": "Deck not found or no permission."}

                    if existing_deck.deckHash == deck_hash:
                        return {"status": False, "message": "No changes detected."}

                    existing_deck.deckJson = deckJson
                    existing_deck.deckHash = deck_hash
                    existing_deck.modified = datetime.now().isoformat()

                    session.commit()
                    return {"status": True, "message": f"Deck '{deckJson.get('name', 'Untitled')}' updated.", "deckID": deck_id}

                else:
                    dup_query = select(deckModel.Tempdeck).where(
                        deckModel.Tempdeck.deckID == deck_id,
                        deckModel.Tempdeck.ownerID == clientID,
                        deckModel.Tempdeck.deleted == False
                    )
                    dup_result = session.execute(dup_query)
                    if dup_result.scalar():
                        return {"status": False, "message": "Duplicate deck already exists."}

                    new_deck = deckModel.Tempdeck(
                        deckID=deck_id,
                        ownerID=clientID,
                        created=datetime.now().isoformat(),
                        deleted=False,
                        deckJson=deckJson,
                        deckHash=deck_hash
                    )
                    session.add(new_deck)

                    session.commit()
                    return {"status": True, "message": f"Deck '{deckJson.get('name', 'Untitled')}' created.", "deckID": deck_id}
                
                