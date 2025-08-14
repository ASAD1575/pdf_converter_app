variable "region" {
  description = "The AWS region where the resources will be deployed."
  type        = string
  default     = "us-east-1"
  
}

variable "efs_name" {
  type = string
  description = "The name of the EFS file system."
  default = "LibreOfficeEFS"
}

variable "subnet_ids" {
  type = list(string)
  description = "List of subnet IDs where the EFS mount targets will be created."
  
}

variable "security_group_id" {
  type = string
  description = "The security group ID to associate with the EFS mount targets."
  
}

variable "vpc_id" {
  type = string
  description = "The ID of the VPC where the EFS mount targets will be created."
}
