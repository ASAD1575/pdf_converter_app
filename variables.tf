variable "s3_key_app" {
  type = string
}

variable "source_code_hash_app" {
  type = string
}

variable "s3_key_layer" {
  type = string
}

variable "source_code_hash_layer" {
  type = string
}

variable "region" {
  type = string
  default = "us-east-1"
}

variable "libreoffice_layer_arn" {
  description = "The ARN of the LibreOffice Lambda Layer for your region and runtime. (Optional - not used in current configuration)"
  type        = string
  default     = ""
  # Example: "arn:aws:lambda:eu-north-1:764866452813:layer:libreoffice-brotli:X"
  # You need to find the correct ARN for your region and the latest version.
  # This layer is crucial for the 'libreoffice' command to work within Lambda.
  
}

variable "source_code_hash_libreoffice_layer" {
  description = "The base64-encoded SHA256 hash of the LibreOffice Lambda Layer package. (Optional - not used in current configuration)"
  type        = string
  default     = ""
}
