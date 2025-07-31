# modules/cloudwatch_logs/outputs.tf

output "log_group_name" {
  description = "The name of the created CloudWatch Log Group."
  value       = aws_cloudwatch_log_group.lambda_log_group.name
}

output "log_group_arn" {
  description = "The ARN of the created CloudWatch Log Group."
  value       = aws_cloudwatch_log_group.lambda_log_group.arn
}
