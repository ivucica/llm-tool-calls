FROM mcr.microsoft.com/vscode/devcontainers/python:3.11

# Install system dependencies
RUN apt-get update && apt-get install -y \
    bash \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set up the working directory
WORKDIR /workspace

# Copy the requirements file and install dependencies
COPY requirements.txt /workspace/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the workspace contents
COPY . /workspace

# Set up the entrypoint
ENTRYPOINT ["/bin/bash"]