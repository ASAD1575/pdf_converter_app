# modules/api_gateway/outputs.tf

output "api_gateway_url" {
  description = "The URL of the deployed API Gateway stage."
  value       = aws_api_gateway_stage.prod_stage.invoke_url
}

output "rest_api_id" {
  description = "The ID of the REST API Gateway."
  value       = aws_api_gateway_rest_api.main_api.id
}
