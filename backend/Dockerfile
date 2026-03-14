FROM python:3.11-slim

# Install docker and kubernetes client for OpenClaw agent
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    lsb-release \
    apt-transport-https \
    ca-certificates \
    && curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update \
    && apt-get install -y docker-ce-cli \
    && curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" \
    && install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl \
    && rm kubectl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy shared logic
COPY backend/requirements.txt backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ backend/
COPY automation/ automation/

WORKDIR /app/backend

# Make sure logs dir exists so we can write to it
RUN mkdir -p /app/logs

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
