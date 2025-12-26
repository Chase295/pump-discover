FROM python:3.11-slim

WORKDIR /app

# Installation der benötigten Pakete
RUN apt-get update && \
    apt-get install -y --no-install-recommends && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir streamlit requests pyyaml docker

# Kopiere App
COPY app.py .

# Streamlit Port
EXPOSE 8501

# Starte Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

