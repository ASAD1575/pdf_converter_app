provider "aws" {
  region = var.region
}

# Data source to get available Availability Zones in the region
data "aws_availability_zones" "available" {
  state = "available"
  # Filter to ensure we get at least 2 AZs for RDS requirement
  filter {
    name   = "zone-type"
    values = ["availability-zone"]
  }
}

# Create a VPC
resource "aws_vpc" "pdf_vpc" {
  cidr_block           = var.cidr_block
  enable_dns_support   = true
  enable_dns_hostnames = true # Essential for RDS endpoint resolution
  tags = {
    Name = "pdf-vpc"
  }
}

# Create Public Subnets (at least 2 for robust architecture)
resource "aws_subnet" "public_subnet" {
  count                   = 2 # Create 2 public subnets
  vpc_id                  = aws_vpc.pdf_vpc.id
  cidr_block              = cidrsubnet(var.cidr_block, 8, count.index) # e.g., 10.0.0.0/24, 10.0.1.0/24
  availability_zone       = data.aws_availability_zones.available.names[count.index] # Distribute across AZs
  map_public_ip_on_launch = true # Public subnets should map public IPs
  tags = {
    Name = "Public Subnet ${count.index}"
  }
}

# Create Private Subnets (at least 2 for RDS AZ coverage)
resource "aws_subnet" "private_subnet" {
  count                   = 2 # Create 2 private subnets
  vpc_id                  = aws_vpc.pdf_vpc.id
  cidr_block              = cidrsubnet(var.cidr_block, 8, count.index + 2) # e.g., 10.0.2.0/24, 10.0.3.0/24
  availability_zone       = data.aws_availability_zones.available.names[count.index] # Distribute across AZs
  map_public_ip_on_launch = false # IMPORTANT: Private subnets should NOT map public IPs
  tags = {
    Name = "Private Subnet ${count.index}"
  }
}

# Create Internet Gateway for Public Subnet access
resource "aws_internet_gateway" "pdf_igw" {
  vpc_id = aws_vpc.pdf_vpc.id
  tags = {
    Name = "pdf Internet Gateway"
  }
}

# Create Elastic IP for NAT Gateway (one per AZ where NAT Gateway is deployed)
resource "aws_eip" "pdf_eip" {
  count = 1 # Only one NAT Gateway for simplicity, could be 2 for high-availability
  tags = {
    Name = "pdf NAT EIP ${count.index}"
  }
}

# Create NAT Gateway in the Public Subnet
resource "aws_nat_gateway" "pdf_nat" {
  count         = 1 # Only one NAT Gateway for simplicity, could be 2 for high-availability
  allocation_id = aws_eip.pdf_eip[count.index].id
  subnet_id     = aws_subnet.public_subnet[count.index].id # NAT Gateway must be in a public subnet
  tags = {
    Name = "pdf NAT Gateway ${count.index}"
  }
  # Add depends_on to ensure IGW is created before NAT Gateway
  depends_on = [aws_internet_gateway.pdf_igw]
}

# Create Public Route Table
resource "aws_route_table" "public_rt" {
  count  = 2 # One route table per public subnet
  vpc_id = aws_vpc.pdf_vpc.id
  tags = {
    Name = "pdf Public Route Table ${count.index}"
  }
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.pdf_igw.id
  }
}

# Associate Public Subnets with Public Route Tables
resource "aws_route_table_association" "public_subnet_association" {
  count          = 2
  subnet_id      = aws_subnet.public_subnet[count.index].id
  route_table_id = aws_route_table.public_rt[count.index].id
}

# Create Private Route Table
resource "aws_route_table" "private_rt" {
  count  = 2 # One route table per private subnet
  vpc_id = aws_vpc.pdf_vpc.id
  tags = {
    Name = "pdf Private Route Table ${count.index}"
  }
  route {
    cidr_block = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.pdf_nat[0].id # All private subnets route through the first NAT Gateway
  }
}

# Associate Private Subnets with Private Route Tables
resource "aws_route_table_association" "private_subnet_association" {
  count          = 2
  subnet_id      = aws_subnet.private_subnet[count.index].id
  route_table_id = aws_route_table.private_rt[count.index].id
}
