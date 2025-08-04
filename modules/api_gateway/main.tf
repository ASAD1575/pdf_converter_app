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

# 2. Create a method for the ROOT path (/) - This is explicitly added to handle base URL requests
resource "aws_api_gateway_method" "root_method" {
  rest_api_id   = aws_api_gateway_rest_api.main_api.id
  resource_id   = aws_api_gateway_rest_api.main_api.root_resource_id # Target the root resource
  http_method   = "ANY" # Catches all HTTP verbs for the root path
  authorization = "NONE" # No authorization for simplicity, adjust as needed
}

# 3. Integrate the ROOT method with the Lambda function
resource "aws_api_gateway_integration" "root_lambda_integration" {
  rest_api_id             = aws_api_gateway_rest_api.main_api.id
  resource_id             = aws_api_gateway_rest_api.main_api.root_resource_id # Target the root resource
  http_method             = aws_api_gateway_method.root_method.http_method
  integration_http_method = "POST" # Lambda proxy integration typically uses POST
  type                    = "AWS_PROXY" # Use AWS_PROXY for Lambda proxy integration
  uri                     = var.lambda_function_invoke_arn # ARN for invoking the Lambda
}


# 4. Create a resource for the catch-all path ({proxy+}) - This handles all sub-paths
resource "aws_api_gateway_resource" "proxy_resource" {
  rest_api_id = aws_api_gateway_rest_api.main_api.id
  parent_id   = aws_api_gateway_rest_api.main_api.root_resource_id
  path_part   = "{proxy+}" # This creates a catch-all path for any sub-paths
}

# 5. Create a method for the catch-all resource (ANY HTTP method)
resource "aws_api_gateway_method" "proxy_method" {
  rest_api_id   = aws_api_gateway_rest_api.main_api.id
  resource_id   = aws_api_gateway_resource.proxy_resource.id
  http_method   = "ANY" # Catches all HTTP verbs (GET, POST, PUT, DELETE, etc.)
  authorization = "NONE" # No authorization for simplicity, adjust as needed
}

# 6. Integrate the catch-all method with the Lambda function
resource "aws_api_gateway_integration" "proxy_lambda_integration" {
  rest_api_id             = aws_api_gateway_rest_api.main_api.id
  resource_id             = aws_api_gateway_resource.proxy_resource.id
  http_method             = aws_api_gateway_method.proxy_method.http_method
  integration_http_method = "POST" # Lambda proxy integration typically uses POST
  type                    = "AWS_PROXY" # Use AWS_PROXY for Lambda proxy integration
  uri                     = var.lambda_function_invoke_arn # ARN for invoking the Lambda
}

# 7. Create a deployment
resource "aws_api_gateway_deployment" "main_deployment" {
  rest_api_id = aws_api_gateway_rest_api.main_api.id
  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_rest_api.main_api.body, 
      aws_api_gateway_method.root_method.id,
      aws_api_gateway_integration.root_lambda_integration.id,
      aws_api_gateway_method.proxy_method.id,
      aws_api_gateway_integration.proxy_lambda_integration.id,
      aws_api_gateway_rest_api.main_api.body, 
      aws_api_gateway_method.root_method.id,
      aws_api_gateway_integration.root_lambda_integration.id,
      aws_api_gateway_method.proxy_method.id,
      aws_api_gateway_integration.proxy_lambda_integration.id,
      aws_api_gateway_method.root_options.id,
      aws_api_gateway_integration.root_options_integration.id,
      aws_api_gateway_method.proxy_options.id,
      aws_api_gateway_integration.proxy_options_integration.id
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }

  # Add explicit dependencies to ensure all methods and integrations are ready
  depends_on = [
    aws_api_gateway_method.root_method,
    aws_api_gateway_integration.root_lambda_integration,
    aws_api_gateway_method.proxy_method,
    aws_api_gateway_integration.proxy_lambda_integration,
    aws_api_gateway_method.root_method,
    aws_api_gateway_integration.root_lambda_integration,
    aws_api_gateway_method.proxy_method,
    aws_api_gateway_integration.proxy_lambda_integration,
    aws_api_gateway_method.root_options,
    aws_api_gateway_integration.root_options_integration,
    aws_api_gateway_method.proxy_options,
    aws_api_gateway_integration.proxy_options_integration,
  ]
}

# 8. Create a stage for the deployment
resource "aws_api_gateway_stage" "prod_stage" {
  deployment_id = aws_api_gateway_deployment.main_deployment.id
  rest_api_id   = aws_api_gateway_rest_api.main_api.id
  stage_name    = "prod" # Common stage name
  description   = "Production stage for PDF Converter API"

  tags = {
    Name = "${var.api_name}-prod-stage"
  }
}

# 9. Grant API Gateway permission to invoke the Lambda function
resource "aws_lambda_permission" "apigw_lambda_permission" {
  statement_id  = "AllowAPIGatewayInvokeLambda"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_function_name # Name of the Lambda function
  principal     = "apigateway.amazonaws.com"

  # The /*/* part is a wildcard for any method on any path
  # This covers both the root method and the proxy method
  source_arn = "arn:aws:execute-api:${var.region}:${data.aws_caller_identity.current.account_id}:${aws_api_gateway_rest_api.main_api.id}/*/*"
}

# --- Existing code remains unchanged above ---

# 10. Enable CORS for ROOT path
resource "aws_api_gateway_method" "root_options" {
  rest_api_id   = aws_api_gateway_rest_api.main_api.id
  resource_id   = aws_api_gateway_rest_api.main_api.root_resource_id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "root_options_integration" {
  rest_api_id = aws_api_gateway_rest_api.main_api.id
  resource_id = aws_api_gateway_rest_api.main_api.root_resource_id
  http_method = aws_api_gateway_method.root_options.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

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

resource "aws_api_gateway_integration_response" "root_options_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.main_api.id
  resource_id = aws_api_gateway_rest_api.main_api.root_resource_id
  http_method = aws_api_gateway_method.root_options.http_method
  status_code = aws_api_gateway_method_response.root_options_response.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }

  response_templates = {
    "application/json" = ""
  }
}

# 11. Enable CORS for {proxy+} path
resource "aws_api_gateway_method" "proxy_options" {
  rest_api_id   = aws_api_gateway_rest_api.main_api.id
  resource_id   = aws_api_gateway_resource.proxy_resource.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "proxy_options_integration" {
  rest_api_id = aws_api_gateway_rest_api.main_api.id
  resource_id = aws_api_gateway_resource.proxy_resource.id
  http_method = aws_api_gateway_method.proxy_options.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

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

resource "aws_api_gateway_integration_response" "proxy_options_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.main_api.id
  resource_id = aws_api_gateway_resource.proxy_resource.id
  http_method = aws_api_gateway_method.proxy_options.http_method
  status_code = aws_api_gateway_method_response.proxy_options_response.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }

  response_templates = {
    "application/json" = ""
  }
}

