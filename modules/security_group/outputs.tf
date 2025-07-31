output "app_sg_id" {
  value = aws_security_group.app_sg.id
}

output "app_security_group_id" {
  description = "The ID of the application security group."
  value       = aws_security_group.app_sg.id
}

output "rds_security_group_id" {
  description = "The ID of the RDS database security group."
  value       = aws_security_group.rds_sg.id
}
