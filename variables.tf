# variable "s3_key_app" {
#   type = string
# }

# variable "source_code_hash_app" {
#   type = string
# }

# variable "s3_key_layer" {
#   type = string
# }

# variable "source_code_hash_layer" {
#   type = string
# }

variable "region" {
  type = string
  default = "us-east-1"
}

variable "secret_key" {
  description = "The secret key for the application."
  type        = string
  default = "SiUtwwXFb8AB3klEityPm45+FS5nv4z0Kei61Lx6"
  
}

variable "app_name" {
  description = "The name of the application, used for naming resources."
  type        = string
  default     = "pdf-converter" 
  
}

variable "image_uri" {
  type = string
  default = "375299695019.dkr.ecr.us-east-1.amazonaws.com/pdf_app_repo"
}