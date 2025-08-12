variable "region" {
  description = "The AWS region to deploy the Lambda function in."
  type        = string
}

variable "function_name" {
  description = "The name for the Lambda function."
  type        = string
  default     = "pdf-converter-lambda"
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs for the Lambda function to connect to the VPC."
  type        = list(string)
}

variable "app_security_group_id" {
  description = "The ID of the application security group to attach to the Lambda function."
  type        = string
}

variable "libreoffice_layer_arn" {
  description = "The ARN of the LibreOffice Lambda Layer for your region and runtime."
  type        = string
  # Example: "arn:aws:lambda:eu-north-1:764866452813:layer:libreoffice-brotli:X"
  # You need to find the correct ARN for your region and the latest version.
  # This layer is crucial for the 'libreoffice' command to work within Lambda.
}

# Database connection environment variables
variable "db_host" {
  description = "The hostname/endpoint of the RDS database."
  type        = string
}

variable "db_name" {
  description = "The name of the database."
  type        = string
}

variable "db_user" {
  description = "The username for the database."
  type        = string
}

variable "db_password" {
  description = "The password for the database."
  type        = string
  sensitive   = true # Mark as sensitive to prevent logging in plaintext
}

variable "db_port" {
  description = "The port for the database."
  type        = string
  default     = "5432"
}

variable "s3_bucket_name" {
  description = "The S3 bucket name for storing and retrieving files."
  type = string
}

variable "source_code_hash_app" {
  description = "The base64-encoded SHA256 hash of the Lambda function's deployment package."
  type        = string
}

variable "source_code_hash_layer" {
  description = "The base64-encoded SHA256 hash of the Lambda function's layer package."
  type        = string
}

variable "s3_key_app" {
  type = string
}

variable "s3_key_layer" {
  type = string
}

variable "source_code_hash_libreoffice_layer" {
  description = "The base64-encoded SHA256 hash of the LibreOffice layer package."
  type        = string
  
}

variable "aws_region" {
  description = "The AWS region where the Lambda function will be deployed."
  type        = string
  default     = "us-east-1"
  
}

variable "aws_account_id" {
  description = "The AWS account ID where the Lambda function will be deployed."
  type        = string
  default     = "375299695019" # Replace with your actual AWS account ID
  
}