# --- STAGE 1: Build dependencies ---
<<<<<<< HEAD
# This stage installs LibreOffice and other dependencies into a base Debian image.
# We're doing this separately to keep the final image clean and small.
FROM debian:bullseye-slim as build

# Install LibreOffice and other necessary tools.
# We separate `apt-get update` and `apt-get install` to leverage Docker's cache.
# If the dependencies don't change, Docker reuses the layer, making the build faster.
=======
# This stage installs LibreOffice and other large dependencies.
FROM debian:bullseye-slim as build

# Install LibreOffice and other necessary tools.
>>>>>>> c2629fe (m)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libreoffice \
        unzip \
        fonts-dejavu \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# --- STAGE 2: Final Lambda Image ---
# This is the final, lean image that will run in AWS Lambda.
<<<<<<< HEAD
# It uses the official Lambda Python 3.10 base image.
FROM public.ecr.aws/lambda/python:3.10

# Set the working directory in the container.
WORKDIR /var/task

# Copy only the LibreOffice binaries and libraries from the build stage.
# This keeps the final image size to a minimum.
=======
FROM public.ecr.aws/lambda/python:3.10

# Set the working directory for the application code.
WORKDIR /var/task

# Copy the LibreOffice binaries and libraries from the build stage.
# This is a critical step that keeps the final image size to a minimum.
>>>>>>> c2629fe (m)
COPY --from=build /usr/bin/libreoffice /usr/bin/libreoffice
COPY --from=build /usr/lib/libreoffice /usr/lib/libreoffice
COPY --from=build /usr/share/fonts /usr/share/fonts
COPY --from=build /usr/share/libreoffice /usr/share/libreoffice

<<<<<<< HEAD
# Install your Python dependencies.
# We copy `requirements.txt` first to cache this layer.
# If requirements don't change, this step is skipped.
COPY requirements.txt .
RUN pip install -r requirements.txt --target .

# Copy the application code into the image.
# This should be the last step to ensure the cache is used.
COPY . .

# Set the command to run your Lambda function.
=======
# Install Python dependencies from your `requirements.txt` file.
# The path is now relative to the root of your project.
COPY pdf_converter_FastAPI_app/requirements.txt .
RUN pip install -r requirements.txt --target .

# Copy your entire application code directory into the image.
COPY pdf_converter_FastAPI_app/ .

# Since you're using FastAPI, you'll need a handler file.
# This command sets the entry point for the Lambda function.
# It assumes a handler function named 'handler' in a file named 'handler.py'.
>>>>>>> c2629fe (m)
CMD ["handler.handler"]
