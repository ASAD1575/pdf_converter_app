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