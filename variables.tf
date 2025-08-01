variable "s3_bucket_name" {
  description = "The name of the S3 bucket to store Lambda code"
  type        = string
  default     = "pdflambdabucket1575"
}

variable "source_code_path" {
  description = "The path to the source code for the Lambda function"
  type        = string
  default     = "pdf_converter_FastAPI_app/"
}
