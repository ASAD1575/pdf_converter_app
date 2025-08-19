provider "aws" {
  region = var.region
}

# Create two EC2 instances using the 'count' meta-argument
# Instance at index 0 will be the public server.
# Instance at index 1 will be the private server.
resource "aws_instance" "servers" {
  count = 2

  ami           = var.ami_id
  instance_type = var.instance_type
  key_name      = var.key_name

  # Use count.index to determine the subnet and public IP association.
  # If the index is 0, use the public subnet and enable a public IP.
  # Otherwise (index 1), use the private subnet and disable the public IP.
  subnet_id                   = count.index == 0 ? var.public_subnet_id : var.private_subnet_id
  associate_public_ip_address = count.index == 0

  # Assign the same security groups to both instances.
  vpc_security_group_ids = var.vpc_security_group_ids

  # Configure the root block device for both instances.
  root_block_device {
    volume_type = "gp3"
    volume_size = var.root_volume_size
  }

  # Use count.index to set a descriptive Name tag.
  tags = {
    Name = "server-${count.index == 0 ? "public" : "private"}"
    Role = count.index == 0 ? "public-server" : "private-server"
  }
}