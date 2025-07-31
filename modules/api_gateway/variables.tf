# modules/api_gateway/variables.tf

variable "region" {
  description = "The AWS region to deploy the API Gateway in."
  type        = string
}

variable "api_name" {
  description = "The name for the API Gateway REST API."
  type        = string
  default     = "pdf-converter-api"
}

variable "lambda_function_name" {
  description = "The name of the Lambda function to integrate with API Gateway."
  type        = string
}

variable "lambda_function_arn" {
  description = "The ARN of the Lambda function to integrate with API Gateway."
  type        = string
}

variable "lambda_function_invoke_arn" {
  description = "The invoke ARN of the Lambda function for API Gateway integration."
  type        = string
}
