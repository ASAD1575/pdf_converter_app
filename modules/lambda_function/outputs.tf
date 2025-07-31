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
