# modules/lambda/outputs.tf

output "function_name" {
  description = "The name of the Lambda function."
  value       = aws_lambda_function.pdf_converter_app.function_name
}

output "function_arn" {
  description = "The ARN of the Lambda function."
  value       = aws_lambda_function.pdf_converter_app.arn
}

output "function_invoke_arn" {
  description = "The ARN to invoke the Lambda function."
  value       = aws_lambda_function.pdf_converter_app.invoke_arn
}

output "ecr_repository_uri" {
  description = "The URI of the ECR repository."
  value       = aws_ecr_repository.app_repo.repository_url
}
