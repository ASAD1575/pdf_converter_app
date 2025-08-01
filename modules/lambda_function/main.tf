# modules/lambda/main.tf

provider "aws" {
  region = var.region
}

# 1. IAM Role for Lambda Function
# This role grants the Lambda function permissions to execute,
# access VPC resources (for RDS), and write logs to CloudWatch.
resource "aws_iam_role" "lambda_exec_role" {
  name = "${var.function_name}-exec-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.function_name}-exec-role"
  }
}

# Attach the basic Lambda execution policy
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Attach the VPC access policy (required for RDS connectivity)
resource "aws_iam_role_policy_attachment" "lambda_vpc_access" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

resource "aws_iam_role_policy" "lambda_s3_access" {
  name = "${var.function_name}-s3-access-policy"
  role = aws_iam_role.lambda_exec_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:DeleteObject",
          "s3:ListBucket" # Needed for some S3 operations, e.g., if you list contents
        ],
        Effect   = "Allow",
        Resource = [
          "arn:aws:s3:::${var.s3_bucket_name}",
          "arn:aws:s3:::${var.s3_bucket_name}/*"
        ]
      }
    ]
  })
}


# --- NEW: 2. AWS Lambda Layer for Python Dependencies ---
# This resource deploys the dependencies.zip file created by Jenkins.
resource "aws_lambda_layer_version" "dependencies_layer" {
  layer_name          = "${var.function_name}-dependencies"
  s3_bucket           = var.s3_bucket_name
  s3_key              = var.dependencies_zip_file_name
  source_code_hash    = var.dependencies_code_hash
  compatible_runtimes = ["python3.10"]

  tags = {
    Name = "${var.function_name}-dependencies-layer"
  }
}


# --- MODIFIED: 3. AWS Lambda Function ---
resource "aws_lambda_function" "pdf_converter_app" {
  function_name = var.function_name
  handler       = "main.app" 
  runtime       = "python3.10"
  role          = aws_iam_role.lambda_exec_role.arn
  timeout       = 300
  memory_size   = 1024

  # The S3 key and hash now point to the application code package
  s3_bucket = var.s3_bucket_name
  s3_key = var.app_zip_file_name
  source_code_hash = var.app_code_hash

  # VPC Configuration (to access RDS)
  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [var.app_security_group_id]
  }

  # Lambda Layers now includes both the new dependencies layer and the LibreOffice layer
  layers = [
    aws_lambda_layer_version.dependencies_layer.arn, # Your new dependencies layer
    var.libreoffice_layer_arn # The original LibreOffice layer
  ]

  # Environment variables for the application (e.g., database connection)
  environment {
    variables = {
      DB_HOST     = var.db_host
      DB_NAME     = var.db_name
      DB_USER     = var.db_user
      DB_PASSWORD = var.db_password
      DB_PORT     = var.db_port
      S3_BUCKET_NAME = var.s3_bucket_name
    }
  }

  tags = {
    Name = var.function_name
  }
}
