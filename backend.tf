terraform {
  backend "s3" {
    bucket         = "pdfappbackend"
    key            = "terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-state-lock-table"
    
  }
}
