# Outputs for the VPC module
output "vpc_id" {
  description = "The ID of the created VPC."
  value       = aws_vpc.pdf_vpc.id
}

output "public_subnet_ids" {
  description = "List of IDs of the public subnets."
  value       = aws_subnet.public_subnet[*].id # Collects all public subnet IDs
}

output "private_subnet_ids" {
  description = "List of IDs of the private subnets."
  value       = aws_subnet.private_subnet[*].id # Collects all private subnet IDs
}