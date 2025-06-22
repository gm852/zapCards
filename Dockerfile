# python base image
FROM python:3.12-slim

# working directory
WORKDIR /app

# system dependencies
RUN apt-get update && \
    apt-get install -y python3-venv && \
    apt-get clean


# application files
COPY . .

# make & activate virtual environment
RUN python -m venv venv && \
    ./venv/bin/pip install --upgrade pip && \
    ./venv/bin/pip install -r req.txt

# Patch the old-style exception in tracerite
RUN sed -i 's/except AttributeError, TypeError:/except (AttributeError, TypeError):/' $(find /app/venv -type f -name inspector.py)

# cp default settings if not present
RUN test -f settings.conf || cp settings.conf.example settings.conf

# port used by the app
EXPOSE 8089

# env variables
ENV OLLAMA_HOST=http://host.docker.internal:11434


# run app
CMD ["venv/bin/python", "run.py", "--port", "8089"]
