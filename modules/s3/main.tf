provider "aws" {
  region = var.region
  
}

# Create S3 Bucket for Static Website Hosting
resource "aws_s3_bucket" "tfstate_bucket" {
  bucket = var.s3_bucket_name
  force_destroy = true

  tags = {
    Name = var.s3_bucket_name
  }
}

# Allow Public Access to the S3 Bucket
resource "aws_s3_bucket_public_access_block" "public_access" {
  bucket = aws_s3_bucket.tfstate_bucket.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

