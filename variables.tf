variable "region" {
  description = "The AWS region to create resources in"
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  description = "The CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "A list of CIDR blocks for the public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "private_subnet_cidrs" {
  description = "A list of CIDR blocks for the private subnets"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
}

variable "ingress_cidrs" {
  description = "A list of CIDR blocks to allow for ingress traffic"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "app_security_group_name" {
  description = "The name of the security group for the Lambda function"
  type        = string
  default     = "pdfconverter-app-sg"
}

variable "db_security_group_name" {
  description = "The name of the security group for the RDS instance"
  type        = string
  default     = "pdfconverter-db-sg"
}

variable "db_name" {
  description = "The name for the RDS database"
  type        = string
  default     = "pdfconverterdb"
}

variable "db_username" {
  description = "The username for the RDS database"
  type        = string
  default     = "dbuser"
}

variable "db_password" {
  description = "The password for the RDS database"
  type        = string
  sensitive   = true
}

variable "db_port" {
  description = "The port for the RDS database"
  type        = number
  default     = 5432
}

variable "function_name" {
  description = "The name of the Lambda function"
  type        = string
  default     = "pdfconverter"
}

variable "s3_bucket_name" {
  description = "The name of the S3 bucket to store Lambda code"
  type        = string
  default     = "pdflambdabucket1575"
}

variable "source_code_path" {
  description = "The path to the source code for the Lambda function"
  type        = string
  default     = "pdf_converter_FastAPI_app/"
}

variable "libreoffice_layer_arn" {
  description = "The ARN of the Lambda layer for LibreOffice"
  type        = string
  default     = "arn:aws:lambda:us-east-1:764866452811:layer:libreoffice-lambda-layer:2"
}
