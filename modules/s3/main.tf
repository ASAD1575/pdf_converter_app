provider "aws" {
  region = var.region
}

resource "aws_s3_bucket" "pdflambdabucket" {
  bucket = var.s3_bucket_name

  tags = {
    name = var.s3_bucket_name
  }
}