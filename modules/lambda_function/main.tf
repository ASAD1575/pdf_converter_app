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
  name = "${var.function_name}-access-policy"
  role = aws_iam_role.lambda_exec_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:DeleteObject"
        ],
        Resource = [
          "arn:aws:s3:::${var.s3_bucket_name}/*"
        ]
      },
      {
        Effect = "Allow",
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Resource = "arn:aws:logs:${var.aws_region}:${var.aws_account_id}:log-group:/aws/lambda/${var.function_name}:*"
      },
      {
        Effect = "Allow",
        Action = "lambda:GetLayerVersion",
        Resource = "arn:aws:lambda:us-east-1:764866452798:layer:libreoffice-gzip:1"
      }
    ]
  })
}

# 2. Lambda Layer for Dependencies (from S3)
# ------------------------------
resource "aws_lambda_layer_version" "python_dependencies" {
  layer_name          = "${var.function_name}-dependencies"
  s3_bucket           = var.s3_bucket_name
  s3_key              = var.s3_key_layer
  compatible_runtimes = ["python3.9"]

  # Helps Terraform detect updates
  source_code_hash = var.source_code_hash_layer
}

resource "aws_lambda_layer_version" "libreoffice_layer" {
  layer_name          = "libreoffice-layer"
  s3_bucket           = var.s3_bucket_name
  s3_key              = "libreoffice-layer.zip"
  compatible_runtimes = ["python3.7", "python3.8", "python3.9", "python3.10"]
  # Helps Terraform detect updates
  source_code_hash = var.source_code_hash_libreoffice_layer
}

# 3. AWS Lambda Function
resource "aws_lambda_function" "pdf_converter_app" {
  function_name = var.function_name
  # package_type  = "Image"
  handler       = "main.handler"              # FAST API wrapped by Mangum
  runtime       = "python3.9" # Specify the runtime version
  role          = aws_iam_role.lambda_exec_role.arn
  timeout       = 300 
  memory_size   = 1536 

  # Code from S3
  s3_bucket         = var.s3_bucket_name
  s3_key            = var.s3_key_app
  source_code_hash  = var.source_code_hash_app

  # VPC Configuration (to access RDS)
  vpc_config {
    subnet_ids         = var.private_subnet_ids           # Lambda should be in private subnets
    security_group_ids = [var.app_security_group_id]      # Attach your application's SG
  }

  # Layers: Python dependencies + LibreOffice
  layers = [
    aws_lambda_layer_version.python_dependencies.arn,
    var.libreoffice_layer_arn
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
      # SERCRET_KEY = var.secret_key
      FASTAPI_ROOT_PATH = "/prod"
      PATH             = "/opt/libreoffice/program:/usr/bin:/bin"
      LD_LIBRARY_PATH  = "/opt/libreoffice/program:/usr/lib:/lib"
      HOME             = "/tmp"
      # Add any other environment variables your app needs
    }
  }

  tags = {
    Name = var.function_name
  }
}
