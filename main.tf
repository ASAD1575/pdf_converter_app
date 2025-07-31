terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.6.0"
    }
  }
}

# Configure the AWS provider
provider "aws" {
  region = "us-east-1"
}

module "vpc" {
  source = "./modules/vpc"
  cidr_block = "10.0.0.0/16"
  region = "us-east-1"
}

module "security_group" {
  source = "./modules/security_group"
  vpc_id = module.vpc.vpc_id
}

module "s3_bucket" {
  source            = "./modules/s3" # Corrected source from "./modules/s3"
  s3_bucket_name    = "pdflambdabucket1575" # Corrected variable name from s3_bucket_name
  region            = "us-east-1"
  # This module is expected to output: bucket_id, bucket_arn
}

module "rds" {
  source            = "./modules/rds"
  region            = "us-east-1"
  identifier        = "pdfconverterdb"
  instance_class    = "db.t3.micro"
  engine            = "postgres"
  engine_version    = "14"
  database_name     = "pdfconverterdb"
  db_username       = "dbuser"
  db_password       = "Subhani786"
  port              = 5432
  security_group    = module.security_group.app_sg_id
  db_subnet_ids     = module.vpc.private_subnet_ids
}

module "lambda_function" {
  source                    = "./modules/lambda_function"
  region                    = "us-east-1"
  function_name             = "pdfconverter"
  source_code_path          = "pdf_converter_FastAPI_app/"
  private_subnet_ids        = module.vpc.private_subnet_ids
  app_security_group_id     = module.security_group.app_security_group_id
  libreoffice_layer_arn     = "arn:aws:lambda:us-east-1:764866452798:layer:libreoffice-gzip:1"
  db_host                   = module.rds.rds_endpoint
  db_name                   = module.rds.db_name
  db_password               = module.rds.db_password
  db_port                   = module.rds.db_port
  db_user                   = module.rds.db_username
  s3_bucket_name            = module.s3_bucket.s3_bucket_id
}
# 
# Add the API Gateway module
module "api_gateway" {
  source      = "./modules/api_gateway"
  region      = "us-east-1" # Use the region from the provider configuration
  api_name    = "pdf-converter-api"
# 
  # These inputs need to come from your Lambda function module's outputs.
  # You'll need to define and deploy your Lambda function (e.g., using a 'lambda' module)
  # and then pass its name, ARN, and invoke ARN here.
  # For now, these are placeholders.
  lambda_function_name       = module.lambda_function.function_name # Replace with actual Lambda function name
  lambda_function_arn        = module.lambda_function.function_arn # Replace with actual Lambda ARN
  lambda_function_invoke_arn = module.lambda_function.function_invoke_arn
}

module "cloudwatch" {
  source = "./modules/cloudwatch"
  region = "us-east-1"
  # Pass the function name from your Lambda module or CloudFormation stack
  function_name = module.lambda_function.function_name # If using Terraform Lambda module
  # OR if using CloudFormation for Lambda:
  # function_name = aws_cloudformation_stack.pdf_converter_lambda_cfn.outputs.FunctionName
  log_retention_in_days = 7 # Set your desired log retention
  environment           = "dev" # Or "prod", etc.
}


# --- Automation for local .env file update ---
resource "null_resource" "update_local_env" {
  depends_on = [
    module.rds,
    module.api_gateway,
    module.s3_bucket, # Explicitly depend on s3_bucket
  ]

  provisioner "local-exec" {
    working_dir = path.module
    command = "sh -c '${path.module}/update_env.sh \"${module.rds.rds_endpoint}\" \"${module.rds.db_name}\" \"${module.rds.db_username}\" \"${module.rds.db_password}\" \"${module.rds.db_port}\" \"${module.s3_bucket.s3_bucket_id}\"'"
  }
}
