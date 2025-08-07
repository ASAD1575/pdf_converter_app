# --- STAGE 1: Build dependencies ---
# Install LibreOffice and other necessary tools.
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

FROM public.ecr.aws/lambda/python:3.10

# Set the working directory for the application code.
WORKDIR /var/task

# Copy the LibreOffice installation from the build stage.
COPY --from=build /usr/bin/libreoffice /usr/bin/libreoffice
COPY --from=build /usr/lib/libreoffice /usr/lib/libreoffice
COPY --from=build /usr/share/fonts /usr/share/fonts
COPY --from=build /usr/share/libreoffice /usr/share/libreoffice

# The path is now relative to the root of your project.
COPY pdf_converter_FastAPI_app/requirements.txt .
RUN pip install -r requirements.txt --target .

# Copy your entire application code directory into the image.
COPY pdf_converter_FastAPI_app/ .

CMD ["handler.handler"]
