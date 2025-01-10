# Start with Ubuntu 22.04 base image
FROM ubuntu:22.04

# Set environment variables to avoid interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Update the package list and install dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    openjdk-11-jre-headless \
    curl \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME for PySpark
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH

# Install PySpark
RUN pip3 install pyspark

# Install Python dependencies
RUN pip3 install --no-cache-dir \
    transformers \
    firebase-admin \
    pandas \
    torch

# Set the working directory
WORKDIR /app

# Copy application files into the container
COPY . /app

# Expose a port for Spark or application monitoring
EXPOSE 4040

# Set the entry point for the application
ENTRYPOINT ["python3", "/app/main.py"]