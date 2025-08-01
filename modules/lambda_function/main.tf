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

# 2. Package the Python application code into a ZIP file
# This data source creates a .zip file from your application's source directory.
# Ensure your main.py, database.py, models.py, utils.py, requirements.txt,
# and any other necessary Python files are in the 'src' directory (or adjust path).
# data "archive_file" "lambda_zip" {
#   type        = "zip"
#   source_dir  = "${path.root}/${var.source_code_path}"
#   output_path = "${path.module}/app_package.zip"
# }

# 3. AWS Lambda Function
resource "aws_lambda_function" "pdf_converter_app" {
  function_name = var.function_name
  handler       = "main.app" # Assuming your FastAPI app instance is named 'app' in main.py
  runtime       = "python3.10" # Must match the Python version in your Dockerfile
  role          = aws_iam_role.lambda_exec_role.arn
  timeout       = 300 # Increase timeout for PDF conversion (max 900 seconds)
  memory_size   = 1024 # Increase memory for LibreOffice (consider 512-2048 MB)

  s3_bucket = var.s3_bucket_name
  s3_key = "pdf_converter_app.zip"

  source_code_hash = var.source_code_hash
  # VPC Configuration (to access RDS)
  vpc_config {
    subnet_ids         = var.private_subnet_ids # Lambda should be in private subnets
    security_group_ids = [var.app_security_group_id] # Attach your application's SG
  }

  # Lambda Layers (for LibreOffice)
  # IMPORTANT: You need a LibreOffice Lambda Layer ARN for your specific region and runtime.
  # You can find pre-built layers (e.g., from Serverless Framework's serverless-libreoffice plugin)
  # or build your own. Example ARN structure: arn:aws:lambda:REGION:ACCOUNT_ID:layer:libreoffice-brotli:VERSION
  layers = [var.libreoffice_layer_arn]

  # Environment variables for the application (e.g., database connection)
  environment {
    variables = {
      DB_HOST     = var.db_host
      DB_NAME     = var.db_name
      DB_USER     = var.db_user
      DB_PASSWORD = var.db_password
      DB_PORT     = var.db_port
      S3_BUCKET_NAME = var.s3_bucket_name
      # Add any other environment variables your app needs
    }
  }

  tags = {
    Name = var.function_name
  }
}
