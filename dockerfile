# This Dockerfile builds a container image for a Python Lambda function.
# It includes LibreOffice, which is required for document conversions.

# --- STAGE 1: Build Stage ---
# This stage is for installing dependencies that may require compiling.
# We'll use a standard Debian-based image for this.
FROM debian:bullseye-slim AS build

# Set environment variables to prevent interactive prompts during apt-get.
ENV DEBIAN_FRONTEND=noninteractive

# Update the package list and install LibreOffice and other necessary packages.
# The 'libreoffice' package is quite large, but we need the full suite.
# 'unzip' and 'fonts-dejavu' are also useful.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    libreoffice \
    unzip \
    fonts-dejavu \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create a symlink for the LibreOffice executable so it can be found easily.
RUN ln -s /usr/bin/libreoffice7.0 /usr/bin/libreoffice

# --- STAGE 2: Final Image Stage ---
# This is the final image that will be deployed to Lambda.
# We start with the official AWS Lambda Python base image.
FROM public.ecr.aws/lambda/python:3.10

# Copy LibreOffice from the build stage into the final image.
# We only copy the necessary files to keep the image as small as possible.
COPY --from=build /usr/lib/libreoffice /usr/lib/libreoffice
COPY --from=build /usr/bin/libreoffice /usr/bin/libreoffice
COPY --from=build /usr/share/fonts /usr/share/fonts

# Set the working directory inside the container.
WORKDIR /var/task

# Copy the requirements.txt file and install Python dependencies.
# We do this before copying the app code to leverage Docker's caching.
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the application code from your local directory into the container.
# The first dot '.' refers to the source directory (where the Dockerfile is).
# The second dot '.' refers to the destination directory (/var/task).
COPY . .

# Set the command for the Lambda function.
# This specifies the entry point for your application.
# `app` is the name of your Python file (e.g., `app.py`).
# `handler` is the name of the handler function within that file.
CMD ["app.handler"]
