terraform {
  backend "s3" {
    bucket         = "masadsubhani8s3bucket204896"
    key            = "terraform.tfstate"
    region         = "eu-north-1"
    dynamodb_table = "terraform-state-lock-table"
    
  }
}
