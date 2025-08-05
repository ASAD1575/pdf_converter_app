# modules/api_gateway/main.tf

provider "aws" {
  region = var.region
}

# Data source to get the current AWS account ID
data "aws_caller_identity" "current" {}

# 1. Create the REST API Gateway
resource "aws_api_gateway_rest_api" "main_api" {
  name        = var.api_name
  description = "API Gateway for the PDF Converter application"

  tags = {
    Name = var.api_name
  }
}

# --- ROOT PATH (/) Configuration ---

# 2. Create an ANY method for the ROOT path (/) to integrate with Lambda
resource "aws_api_gateway_method" "root_method" {
  rest_api_id   = aws_api_gateway_rest_api.main_api.id
  resource_id   = aws_api_gateway_rest_api.main_api.root_resource_id
  http_method   = "ANY"
  authorization = "NONE"
}

# 3. Integrate the ROOT ANY method with the Lambda function
resource "aws_api_gateway_integration" "root_lambda_integration" {
  rest_api_id             = aws_api_gateway_rest_api.main_api.id
  resource_id             = aws_api_gateway_rest_api.main_api.root_resource_id
  http_method             = aws_api_gateway_method.root_method.http_method
  integration_http_method = "POST" # Lambda proxy integration typically uses POST
  type                    = "AWS_PROXY" # Use AWS_PROXY for Lambda proxy integration
  uri                     = var.lambda_function_invoke_arn
}

# 4. Add a method response for the ROOT ANY method to include CORS headers
# This ensures that actual responses from Lambda also carry the CORS header.
resource "aws_api_gateway_method_response" "root_any_method_response" {
  rest_api_id = aws_api_gateway_rest_api.main_api.id
  resource_id = aws_api_gateway_rest_api.main_api.root_resource_id
  http_method = aws_api_gateway_method.root_method.http_method
  status_code = "200" # Assuming a 200 OK response
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

# 5. Create an OPTIONS method for the ROOT path (/) for CORS preflight requests
resource "aws_api_gateway_method" "root_options" {
  rest_api_id   = aws_api_gateway_rest_api.main_api.id
  resource_id   = aws_api_gateway_rest_api.main_api.root_resource_id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

# 6. Create a MOCK integration for the ROOT OPTIONS method (for CORS preflight)
resource "aws_api_gateway_integration" "root_options_integration" {
  rest_api_id = aws_api_gateway_rest_api.main_api.id
  resource_id = aws_api_gateway_rest_api.main_api.root_resource_id
  http_method = aws_api_gateway_method.root_options.http_method
  type        = "MOCK"
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

# 7. Define the method response for the ROOT OPTIONS method, including CORS headers
resource "aws_api_gateway_method_response" "root_options_response" {
  rest_api_id = aws_api_gateway_rest_api.main_api.id
  resource_id = aws_api_gateway_rest_api.main_api.root_resource_id
  http_method = aws_api_gateway_method.root_options.http_method
  status_code = "200"
  response_models = {
    "application/json" = "Empty"
  }
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

# 8. Define the integration response for the ROOT OPTIONS method, setting CORS header values
resource "aws_api_gateway_integration_response" "root_options_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.main_api.id
  resource_id = aws_api_gateway_rest_api.main_api.root_resource_id
  http_method = aws_api_gateway_method.root_options.http_method
  status_code = aws_api_gateway_method_response.root_options_response.status_code
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'" # Include all common methods
    "method.response.header.Access-Control-Allow-Origin"  = "'*'" # IMPORTANT: Restrict this to your frontend domain in production
  }
  depends_on = [aws_api_gateway_integration.root_options_integration]
}

# --- PROXY PATH ({proxy+}) Configuration ---

# 9. Create a resource for the catch-all path ({proxy+}) - This handles all sub-paths
resource "aws_api_gateway_resource" "proxy_resource" {
  rest_api_id = aws_api_gateway_rest_api.main_api.id
  parent_id   = aws_api_gateway_rest_api.main_api.root_resource_id
  path_part   = "{proxy+}"
}

# 10. Create an ANY method for the catch-all resource ({proxy+}) to integrate with Lambda
resource "aws_api_gateway_method" "proxy_method" {
  rest_api_id   = aws_api_gateway_rest_api.main_api.id
  resource_id   = aws_api_gateway_resource.proxy_resource.id
  http_method   = "ANY"
  authorization = "NONE"
}

# 11. Integrate the PROXY ANY method with the Lambda function
resource "aws_api_gateway_integration" "proxy_lambda_integration" {
  rest_api_id             = aws_api_gateway_rest_api.main_api.id
  resource_id             = aws_api_gateway_resource.proxy_resource.id
  http_method             = aws_api_gateway_method.proxy_method.http_method
  integration_http_method = "POST" # Lambda proxy integration typically uses POST
  type                    = "AWS_PROXY" # Use AWS_PROXY for Lambda proxy integration
  uri                     = var.lambda_function_invoke_arn
}

# 12. Add a method response for the PROXY ANY method to include CORS headers
resource "aws_api_gateway_method_response" "proxy_any_method_response" {
  rest_api_id = aws_api_gateway_rest_api.main_api.id
  resource_id = aws_api_gateway_resource.proxy_resource.id
  http_method = aws_api_gateway_method.proxy_method.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

# 13. Create an OPTIONS method for the catch-all resource ({proxy+}) for CORS preflight requests
resource "aws_api_gateway_method" "proxy_options" {
  rest_api_id   = aws_api_gateway_rest_api.main_api.id
  resource_id   = aws_api_gateway_resource.proxy_resource.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

# 14. Create a MOCK integration for the PROXY OPTIONS method (for CORS preflight)
resource "aws_api_gateway_integration" "proxy_options_integration" {
  rest_api_id = aws_api_gateway_rest_api.main_api.id
  resource_id = aws_api_gateway_resource.proxy_resource.id
  http_method = aws_api_gateway_method.proxy_options.http_method
  type        = "MOCK"
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

# 15. Define the method response for the PROXY OPTIONS method, including CORS headers
resource "aws_api_gateway_method_response" "proxy_options_response" {
  rest_api_id = aws_api_gateway_rest_api.main_api.id
  resource_id = aws_api_gateway_resource.proxy_resource.id
  http_method = aws_api_gateway_method.proxy_options.http_method
  status_code = "200"
  response_models = {
    "application/json" = "Empty"
  }
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

# 16. Define the integration response for the PROXY OPTIONS method, setting CORS header values
resource "aws_api_gateway_integration_response" "proxy_options_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.main_api.id
  resource_id = aws_api_gateway_resource.proxy_resource.id
  http_method = aws_api_gateway_method.proxy_options.http_method
  status_code = aws_api_gateway_method_response.proxy_options_response.status_code
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'" # Include all common methods
    "method.response.header.Access-Control-Allow-Origin"  = "'*'" # IMPORTANT: Restrict this to your frontend domain in production
  }
  depends_on = [aws_api_gateway_integration.proxy_options_integration]
}

# --- Deployment and Stage ---

# 17. Create a deployment for the API Gateway
# Triggers ensure a new deployment happens when relevant API Gateway configurations change.
resource "aws_api_gateway_deployment" "main_deployment" {
  rest_api_id = aws_api_gateway_rest_api.main_api.id
  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_method.root_method.id,
      aws_api_gateway_integration.root_lambda_integration.id,
      aws_api_gateway_method_response.root_any_method_response.id,
      aws_api_gateway_method.root_options.id,
      aws_api_gateway_integration.root_options_integration.id,
      aws_api_gateway_method_response.root_options_response.id,
      aws_api_gateway_integration_response.root_options_integration_response.id,
      aws_api_gateway_resource.proxy_resource.id,
      aws_api_gateway_method.proxy_method.id,
      aws_api_gateway_integration.proxy_lambda_integration.id,
      aws_api_gateway_method_response.proxy_any_method_response.id,
      aws_api_gateway_method.proxy_options.id,
      aws_api_gateway_integration.proxy_options_integration.id,
      aws_api_gateway_method_response.proxy_options_response.id,
      aws_api_gateway_integration_response.proxy_options_integration_response.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }

  # Explicit dependencies to ensure all methods and integrations are created before deployment
  depends_on = [
    aws_api_gateway_method.root_method,
    aws_api_gateway_integration.root_lambda_integration,
    aws_api_gateway_method_response.root_any_method_response,
    aws_api_gateway_method.root_options,
    aws_api_gateway_integration.root_options_integration,
    aws_api_gateway_method_response.root_options_response,
    aws_api_gateway_integration_response.root_options_integration_response,
    aws_api_gateway_resource.proxy_resource,
    aws_api_gateway_method.proxy_method,
    aws_api_gateway_integration.proxy_lambda_integration,
    aws_api_gateway_method_response.proxy_any_method_response,
    aws_api_gateway_method.proxy_options,
    aws_api_gateway_integration.proxy_options_integration,
    aws_api_gateway_method_response.proxy_options_response,
    aws_api_gateway_integration_response.proxy_options_integration_response,
  ]
}

# 18. Create a stage for the deployment (e.g., 'prod')
resource "aws_api_gateway_stage" "prod_stage" {
  deployment_id = aws_api_gateway_deployment.main_deployment.id
  rest_api_id   = aws_api_gateway_rest_api.main_api.id
  stage_name    = "prod"
  description   = "Production stage for PDF Converter API"

  tags = {
    Name = "${var.api_name}-prod-stage"
  }
}

# --- Lambda Permissions ---

# 19. Grant API Gateway permission to invoke the Lambda function
resource "aws_lambda_permission" "apigw_lambda_permission" {
  statement_id  = "AllowAPIGatewayInvokeLambda"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  # The source_arn allows invocation from any method on any path within this API Gateway
  source_arn = "arn:aws:execute-api:${var.region}:${data.aws_caller_identity.current.account_id}:${aws_api_gateway_rest_api.main_api.id}/*/*"
}
