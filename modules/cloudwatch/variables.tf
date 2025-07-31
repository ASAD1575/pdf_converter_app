# modules/cloudwatch_logs/variables.tf

variable "region" {
  description = "The AWS region."
  type        = string
}

variable "function_name" {
  description = "The name of the Lambda function for which to create the log group."
  type        = string
}

variable "log_retention_in_days" {
  description = "The number of days to retain log events in the log group."
  type        = number
  default     = 7 # Default to 30 days retention
  # Allowed values for CloudWatch Log Group retention:
  # 1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653
}

variable "environment" {
  description = "The deployment environment (e.g., dev, staging, prod)."
  type        = string
  default     = "dev"
}
