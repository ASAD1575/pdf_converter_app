output "private_server_ip" {
  description = "The name of the EC2 instance."
  value       = aws_instance.private_server.private_ip
  
}

output "public_server_ip" {
  description = "The public IP of the EC2 instance."
  value       = aws_instance.public_server.public_ip
  
}

