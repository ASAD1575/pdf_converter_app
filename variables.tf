variable "region" {
  type = string
  default = "us-east-1"
}

variable "s3_key" {
  type = string
}
variable "app_zip_file_name" {
  type = string
}

variable "app_code_hash" {
  type = string
}

variable "dependencies_zip_file_name" {
  type = string
}

variable "dependencies_code_hash" {
  type = string
}
