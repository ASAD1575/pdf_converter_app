output "s3_bucket_name" {
  value = aws_s3_bucket.pdflambdabucket.bucket
}

output "s3_bucket_id" {
  value = aws_s3_bucket.pdflambdabucket.id
}

output "s3_bucket_arn" {
  value = aws_s3_bucket.pdflambdabucket.arn
}