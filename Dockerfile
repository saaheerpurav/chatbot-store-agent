# Set base image (host OS)
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any dependencies

RUN python3 -m pip install -r requirements.txt --no-cache-dir
# Copy the content of the local src directory to the working directory

COPY . .

# By default, listen on port 80
EXPOSE 80

# Specify the command to run on container start
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]



# docker system prune
# docker build -t agent-container .
# docker run -p 80:80 --env-file ./.env agent-container

# docker tag agent-container us-east1-docker.pkg.dev/durable-height-427320-e6/agent-container/agent-container
# docker push us-east1-docker.pkg.dev/durable-height-427320-e6/agent-container/agent-container
