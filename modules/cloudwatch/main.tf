# modules/cloudwatch_logs/main.tf

provider "aws" {
  region = var.region
}

# CloudWatch Log Group for the Lambda function
# AWS Lambda automatically creates a log group named /aws/lambda/<function-name>
# This resource allows us to manage its properties (like retention) explicitly.
resource "aws_cloudwatch_log_group" "lambda_log_group" {
  name              = "/aws/lambda/${var.function_name}" # Standard Lambda log group naming convention
  retention_in_days = var.log_retention_in_days

  tags = {
    Name        = "${var.function_name}-logs"
    Environment = var.environment # Good practice to include environment tag
  }
}
