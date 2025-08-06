# --- STAGE 1: Build dependencies ---
# This stage installs LibreOffice and other large dependencies.
FROM debian:bullseye-slim as build

# Install LibreOffice and other necessary tools.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libreoffice \
        unzip \
        fonts-dejavu \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# --- STAGE 2: Final Lambda Image ---
# This is the final, lean image that will run in AWS Lambda.
FROM public.ecr.aws/lambda/python:3.10

# Set the working directory for the application code.
WORKDIR /var/task

# Copy the LibreOffice binaries and libraries from the build stage.
# This is a critical step that keeps the final image size to a minimum.
COPY --from=build /usr/bin/libreoffice /usr/bin/libreoffice
COPY --from=build /usr/lib/libreoffice /usr/lib/libreoffice
COPY --from=build /usr/share/fonts /usr/share/fonts
COPY --from=build /usr/share/libreoffice /usr/share/libreoffice

# Install Python dependencies from your `requirements.txt` file.
# The path is now relative to the root of your project.
COPY pdf_converter_FastAPI_app/requirements.txt .
RUN pip install -r requirements.txt --target .

# Copy your entire application code directory into the image.
COPY pdf_converter_FastAPI_app/ .

# Since you're using FastAPI, you'll need a handler file.
# This command sets the entry point for the Lambda function.
# It assumes a handler function named 'handler' in a file named 'handler.py'.
CMD ["handler.handler"]
