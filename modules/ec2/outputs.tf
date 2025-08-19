# The outputs for the instances can also be simplified.
output "instance_ids" {
  description = "IDs of the created EC2 instances"
  value       = aws_instance.servers[*].id
}

output "public_ip" {
  description = "The public IP address of the public server"
  value       = aws_instance.servers[0].public_ip
}

output "private_ip" {
  description = "The private IP address of the private server"
  value       = aws_instance.servers[1].private_ip
}