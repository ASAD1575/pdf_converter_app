# modules/ec2_pair/variables.tf

variable "ami_id" {
  description = "The AMI ID for the EC2 instances."
  type        = string
}

variable "instance_type" {
  description = "The instance type for the EC2 instances (e.g., t2.micro)."
  type        = string
}

variable "public_subnet_id" {
  description = "The ID of the public subnet to launch the EC2 instance in."
  type        = string
}

variable "private_subnet_id" {
  description = "The ID of the private subnet to launch the EC2 instance in."
  type        = string
}

variable "key_name" {
  description = "The name of the EC2 Key Pair to allow SSH access."
  type        = string
}

variable "vpc_security_group_ids" {
  description = "A list of security group IDs to associate with the instances."
  type        = list(string)
}