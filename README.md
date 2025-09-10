# PDF Converter App — FastAPI + Serverless + Terraform + Jenkins CI/CD

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)](https://fastapi.tiangolo.com/)
[![Terraform](https://img.shields.io/badge/Terraform-1.0+-623CE4.svg)](https://www.terraform.io/)
[![AWS Lambda](https://img.shields.io/badge/AWS%20Lambda-Serverless-orange.svg)](https://aws.amazon.com/lambda/)
[![Jenkins](https://img.shields.io/badge/Jenkins-CI%2FCD-red.svg)](https://www.jenkins.io/)
[![Docker](https://img.shields.io/badge/Docker-%F0%9F%90%B3-blue.svg)](https://www.docker.com/)

A serverless PDF converter built with FastAPI, deployed on AWS Lambda, with infrastructure managed via Terraform and automated CI/CD powered by Jenkins using Docker and Terraform.

## Project Overview
This project enables document conversion (e.g., DOCX, XLSX) to PDF via a simple REST API built on FastAPI, deployed serverlessly on AWS Lambda. It uses a custom LibreOffice Lambda layer for conversions and automates deployment using a Jenkins pipeline and Terraform.

### Key components:
- **FastAPI app** (pdf_converter_FastAPI_app/) — handles conversion logic
- **Terraform** (modules/, main.tf, variables.tf, etc.) — defines AWS infrastructure
- **Jenkins pipeline** (Jenkinsfile_Docker) — builds, deploys, and orchestrates CI/CD
- **Dockerfile** — builds the application and dependencies
- **Modular Terraform modules** for API Gateway, Lambda, S3, CloudWatch, RDS (optional), VPC, and security setups

## 📂 Project Structure

```
pdf_converter_app/
├── pdf_converter_FastAPI_app/
│   ├── main.py              # Main FastAPI app
│   ├── database.py          # Database connection and user management
│   ├── models.py            # Data models
│   ├── utils.py             # Utility functions
│   ├── requirements.txt     # Python dependencies
│   ├── templates/           # HTML templates for web interface
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── dashboard.html
│   │   ├── download.html
│   │   ├── forgot_password.html
│   │   ├── success.html
│   │   └── img.png
│   └── uploads/             # Directory for uploaded files
├── modules/                 # Terraform modules
│   ├── api_gateway/
│   ├── lambda_function/
│   ├── s3/
│   ├── vpc/
│   └── ...
├── main.tf                  # Main Terraform configuration
├── variables.tf             # Terraform variables
├── outputs.tf               # Terraform outputs
├── backend.tf               # Terraform backend configuration
├── Jenkinsfile_Docker       # Jenkins pipeline script
├── dockerfile               # Docker build file
├── .gitignore               # Git ignore file
└── README.md                # This file
```

## Application Details

### Purpose
The PDF Converter App is a web-based application that allows users to convert Microsoft Word documents (.docx) to PDF format. It provides both a REST API for programmatic access and a user-friendly web interface for manual conversions. The application is designed for scalability and cost-efficiency by leveraging serverless architecture on AWS.

### Key Features
- **Document Conversion**: Upload .docx files and convert them to PDF using LibreOffice.
- **User Authentication**: Secure login and registration system with password reset functionality.
- **File Management**: Store original documents and converted PDFs in AWS S3.
- **Web Interface**: Intuitive dashboard for uploading files, viewing conversion history, and downloading results.
- **API Access**: RESTful API endpoints for integration with other systems.
- **Serverless Deployment**: Runs on AWS Lambda for automatic scaling and minimal operational overhead.
- **CI/CD Automation**: Automated build, test, and deployment using Jenkins and Docker.

### Technology Stack
- **Backend**: FastAPI (Python web framework), Uvicorn (ASGI server)
- **Conversion Engine**: LibreOffice (via custom Lambda layer)
- **Database**: PostgreSQL/MySQL (via AWS RDS for user management)
- **Storage**: AWS S3 (for file uploads and converted PDFs)
- **Infrastructure**: Terraform (IaC), AWS Lambda, API Gateway, VPC, CloudWatch
- **CI/CD**: Jenkins, Docker
- **Frontend**: Jinja2 templates, HTML/CSS/JS (basic web interface)
- **Other**: Mangum (Lambda adapter), Boto3 (AWS SDK), SQLAlchemy (ORM)

### Architecture
The application follows a serverless architecture:
1. **API Gateway**: Receives HTTP requests and routes them to Lambda functions.
2. **Lambda Function**: Executes the FastAPI app, handles file processing, and interacts with S3/RDS.
3. **S3 Buckets**: Store uploaded .docx files and generated PDFs.
4. **RDS Database**: Manages user accounts and session data.
5. **EFS (Optional)**: Mounts LibreOffice binaries for Lambda layer.
6. **CloudWatch**: Monitors logs and performance metrics.

### Workflow
1. User registers/logs in via the web interface.
2. Uploads a .docx file through the dashboard or API.
3. Application validates the file and stores it in S3.
4. Triggers LibreOffice conversion in the Lambda environment.
5. Saves the converted PDF back to S3.
6. Provides a download link or direct access to the PDF.
7. Logs all activities for monitoring and debugging.

### Security Considerations
- User authentication with secure password hashing.
- File type validation to prevent malicious uploads.
- AWS IAM roles with least-privilege access.
- HTTPS encryption for all communications.
- Environment variable management for sensitive data.

## Table of Contents
1. Prerequisites
2. Local Setup & Run
3. Terraform Infrastructure Deployment
4. Jenkins CI/CD Pipeline Setup
5. Credentials Needed for Jenkins
6. Clean Up
7. API Endpoints
8. Summary

## 1. Prerequisites
- Python 3.9+
- Terraform (installed and AWS credentials configured)
- Docker (installed for building Lambda layers)
- Jenkins (server with Docker and Terraform installed as Jenkins agents)

## 2. Local Setup & Run
1. **Clone the repo:**
    ```
    git clone https://github.com/ASAD1575/pdf_converter_app.git
    cd pdf_converter_app
    ```

2. **Install dependencies:**
    ```
    cd pdf_converter_FastAPI_app
    pip install -r requirements.txt
    ```

3. **Run app locally:**
    ```
    uvicorn main:app --reload
    ```
    - Open http://localhost:8000/docs
    to use the automatically-generated Swagger UI for conversion endpoints.

4. **(Optional) Run with Docker:**
    ```
    docker build -t pdf-converter-app .
    docker run -p 5000:5000 pdf-converter-app
    ```
    - Open http://localhost:5000/docs for the Swagger UI.

## 3. Terraform Infrastructure Deployment

1. **Configure variables** in variables.tf:

- AWS region, environment name, S3 bucket names, etc.

2. **Deploy infrastructure:**
    ```
    cd pdf_converter_app
    terraform init
    terraform plan
    terraform apply
    ```

- This will create required AWS resources (API Gateway, Lambda, VPC, etc.)

- The output will include the API Gateway URL to invoke the app.

3. **Validate:**

    Visit the API URL to test document conversion in the cloud environment.

## 4. Jenkins CI/CD Pipeline Setup

The Jenkinsfile_Docker automates:

- Building a Docker container for the LibreOffice Lambda layer

- Uploading the Lambda layer artifact to S3 and publishing it

- Packaging the FastAPI app and uploading it

- Running terraform apply and outputting deployment info (e.g., API URL)

**Steps:**

1. Create a new **Pipeline** job in Jenkins.

2. Connect to this GitHub repository.

3. Ensure Jenkins agents have Docker, AWS CLI, and Terraform installed.

4. Set needed environment variables (below).

5. Run the pipeline — Jenkins will deploy your app automatically.

## 5. Credentials Needed for Jenkins

Ensure the following credentials are configured in Jenkins (via "Manage Jenkins" → "Credentials"):

| Credential Key | Description |
| --- | --- |
| AWS_ACCESS_KEY_ID | Your AWS IAM access key with permissions to manage AWS resources and publish Lambda layers |
| AWS_SECRET_ACCESS_KEY | The corresponding AWS secret key |
| DOCKERHUB_USERNAME (optional) | If you push Docker images to DockerHub in the pipeline |
| DOCKERHUB_PASSWORD (optional) | DockerHub access token or password |
| S3_BUCKET_NAME | Destination bucket for layer and code uploads (or set in Terraform variables) |

## 6. Clean Up

When you're done and want to avoid AWS charges:

```
terraform destroy
```

Also remove layer artifacts or Docker images as needed.

## 7. API Endpoints

### Convert DOCX to PDF

- **POST** `/convert`
- Upload a `.docx` file to convert it to PDF.
- Returns a JSON response with a `file_id` for the converted PDF.

### Download Converted PDF

- **GET** `/download/{file_id}`
- Downloads the converted PDF file using the `file_id`.

### Authentication & User Management

- **GET** `/register` - Registration form
- **POST** `/register` - Register a new user
- **GET** `/` - Login form
- **POST** `/` - Login user
- **GET** `/forgot_password` - Password reset form
- **POST** `/reset_password_direct` - Reset password

### Dashboard

- **GET** `/dashboard` - User dashboard page

## 8. Summary

This setup enables a fully automated workflow:

- FastAPI app deployed serverlessly via Terraform
- Automated CI/CD using Jenkins and Docker
- Minimal credentials management
- Easily testable locally and deploys consistently in AWS
