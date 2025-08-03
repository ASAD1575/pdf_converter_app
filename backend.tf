terraform {
  backend "s3" {
    bucket         = "pdflambdabucket1575"
    key            = "terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-state-lock-table"
    
  }
}
