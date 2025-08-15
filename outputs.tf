# Optional: Output the API Gateway URL for easy access
output "api_gateway_url" {
  description = "The URL of the deployed API Gateway stage."
  value       = module.api_gateway.api_gateway_url
}

# Optional: Output the RDS endpoint for easy access
output "rds_endpoint" {
  description = "The connection endpoint for the RDS instance."
  value       = module.rds.rds_endpoint # Assuming your RDS module outputs its endpoint
}

# Optional: Output the RDS database name for environment variables
output "rds_db_name" {
  description = "The database name for the RDS instance."
  value       = module.rds.db_name # Assuming your RDS module outputs its db_name
}

# Optional: Output the RDS username for environment variables
output "rds_db_username" {
  description = "The username for the RDS instance."
  value       = module.rds.db_username # Assuming your RDS module outputs its db_username
}

output "rds_db_password" {
  description = "The password for the RDS instance."
  value       = module.rds.db_password
  sensitive   = true # Mark as sensitive to prevent showing in plaintext outputs
}

output "rds_db_port" {
  description = "The port for the RDS instance."
  value       = module.rds.db_port
}

# Optional: Output the application security group ID, useful for attaching to EC2/Lambda
output "app_security_group_id" {
  description = "The ID of the application security group."
  value       = module.security_group.app_security_group_id
}

output "lambda_function_name" {
  description = "The name of the deployed Lambda function."
  value       = module.lambda_function.function_name
}

# Add CloudWatch Logs outputs
output "lambda_log_group_name" {
  description = "The name of the Lambda function's CloudWatch Log Group."
  value       = module.cloudwatch.log_group_name
}

output "lambda_function_arn" {
  description = "The ARN of the deployed Lambda function."
  value       = module.lambda_function.function_arn
}

output "lambda_log_group_arn" {
  description = "The ARN of the Lambda function's CloudWatch Log Group."
  value       = module.cloudwatch.log_group_arn
}

output "vpc_id" {
  value = module.vpc.vpc_id
}

output "name" {
  description = "The name of the EFS file system."
  value       = module.efs.name
  
}

output "file_system_dns" {
  description = "The DNS name of the EFS file system."
  value       = module.efs.file_system_dns
  
}

output "efs_access_point_arn" {
  value = module.efs.efs_access_point_arn
  description = "The ARN of the EFS access point."
}
