provider "aws" {
  region = var.region
}
# Create DynamoDB Table for State Locking
resource "aws_dynamodb_table" "terraform_state_lock" {
  name         = "terraform-state-lock-table"
  billing_mode = "PROVISIONED"
  read_capacity  = 5
  write_capacity = 5
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name = "pdfconverterappdynamodbtable"
  }
  
}
