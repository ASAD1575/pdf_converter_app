# This file is for the ec2_pair module

provider "aws" {
  region = var.region # Ensure this matches your provider configuration
}

# Define the configuration for each instance using a local variable
locals {
  instance_config = {
    public = {
      name             = "public-server"
      subnet_id        = var.public_subnet_id
      public_ip_enable = true
    }
    private = {
      name             = "private-server"
      subnet_id        = var.private_subnet_id
      public_ip_enable = false
    }
  }
}

# Create the EC2 instances based on the configuration map
resource "aws_instance" "servers" {
  for_each = local.instance_config

  ami                    = var.ami_id
  instance_type          = var.instance_type
  subnet_id              = each.value.subnet_id
  key_name               = var.key_name
  vpc_security_group_ids = var.vpc_security_group_ids

  root_block_device {
    volume_type = "gp3"
    volume_size = var.root_volume_size
  }

  associate_public_ip_address = each.value.public_ip_enable

  tags = {
    Name = each.value.name
    Role = each.key
  }
}
