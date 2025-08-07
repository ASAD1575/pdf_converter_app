Serverless PDF Converter with FastAPI and Jenkins CI/CD:

This repository contains the infrastructure and application code for a serverless PDF converter, built with FastAPI and deployed on AWS. The project utilizes a modular Terraform structure for infrastructure management and a Jenkins pipeline for continuous integration and continuous deployment (CI/CD).

🚀 Project Overview:

The core functionality is a FastAPI application that converts documents (e.g., DOCX, XLSX) into PDFs. This application runs on AWS Lambda. To handle the document conversion, a custom AWS Lambda Layer is created that includes a full installation of LibreOffice. The entire CI/CD process is automated using a Jenkins pipeline.

Key Components:

FastAPI Application (pdf_converter_FastAPI_app): The main application logic for document conversion.

Modular Terraform: Infrastructure as Code (IaC) is managed using a modular approach to logically separate different AWS resources.

Jenkins Pipeline (Jenkinsfile): Automates the build, deployment, and update process.

LibreOffice Lambda Layer: A custom AWS Lambda layer containing LibreOffice to enable document conversion within the Lambda environment.

📁 File Structure:

The project is organized with a clear separation of concerns.

.
├── modules/
│   ├── api_gateway/
│   ├── cloudwatch/
│   ├── lambda_function/
│   ├── rds/
│   ├── s3/
│   ├── security_group/
│   └── vpc/
├── pdf_converter_FastAPI_app/
│   ├── templates/
│   ├── uploads/
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── requirements.txt
│   └── utils.py
├── .gitignore
├── Jenkinsfile_Docker
├── main.tf
├── outputs.tf
└── variables.tf


🏗️ Modular Terraform:

The Terraform configuration is organized into modules to promote reusability and maintainability. The main.tf file in the root directory ties all these modules together.

modules/api_gateway: Defines the API Gateway resources to expose the Lambda function via an HTTP endpoint.

modules/cloudwatch: Configures CloudWatch for logging and monitoring of the Lambda function.

modules/lambda_function: Manages the AWS Lambda function, including its role and permissions.

modules/rds: (If applicable) Contains resources for an RDS database.

modules/s3: Manages the S3 buckets used for storing application code and layers.

modules/security_group: Defines the network security groups for controlling traffic to the resources.

modules/vpc: Configures the Virtual Private Cloud (VPC) and its components like subnets and route tables.

main.tf: The root module that instantiates and connects all the sub-modules.

variables.tf: Contains all the variables for the root module.

outputs.tf: Defines the output values (like the API Gateway URL) that can be easily retrieved after deployment.

⚙️ Jenkins CI/CD Pipeline:

The Jenkinsfile orchestrates the entire deployment process. This pipeline is designed to automatically build the application and its dependencies, publish the LibreOffice layer, and deploy the entire infrastructure with Terraform.

Stages:
Initialize Variables: Sets up necessary environment variables like the host user and group IDs for file permissions.

Checkout & Build: Clones the Git repository (https://github.com/vladholubiev/serverless-libreoffice.git) and uses docker-compose to build the LibreOffice Lambda layer, which is essential for the conversion logic.

Publish Lambda Layer: Uses the AWS CLI to publish the layers.zip artifact as a new version of the Lambda layer on AWS. The ARN of this new version is stored in the LAYER_VERSION_ARN environment variable.

Upload to S3: The layers.zip artifact is uploaded to an S3 bucket for persistent storage.

Build Lambda Packages: A Docker container is used to build the main application package (app_package.zip) and its Python dependencies (dependencies_layer.zip). These are then stashed for use in the next stage.

Terraform Deploy: This is the final deployment stage. It un-stashes the application and dependency zip files, calculates their SHA256 hashes for versioning, uploads them to S3, and then runs terraform apply to deploy the entire infrastructure. The ARN from the Lambda layer publication stage is passed as a variable to Terraform.

Post-Deployment Info: After a successful deployment, this stage retrieves the API Gateway URL from the Terraform outputs and prints it to the Jenkins console.

🚀 Getting Started:

Clone the Repository:
git clone <https://github.com/ASAD1575/pdf_converter_app.git>

Configure Jenkins:

Set up a Jenkins pipeline with a Git SCM pointing to this repository.

Configure AWS credentials in Jenkins (AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY).

Run the Pipeline:

Trigger a build of the Jenkins pipeline.

This setup ensures that any change pushed to the repository will automatically trigger a new build and deployment, providing a robust and efficient CI/CD workflow.

Feel free to customize this README.md to include more specific details about your project, such as how to run the application locally or how to configure the Terraform variables.