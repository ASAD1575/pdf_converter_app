# modules/rds/outputs.tf

output "rds_endpoint" {
  description = "The connection endpoint (hostname) of the RDS instance."
  value       = aws_db_instance.pdf_rds_instance.address
}

output "db_name" {
  description = "The name of the database."
  value       = aws_db_instance.pdf_rds_instance.db_name
}

output "db_username" {
  description = "The username for the database."
  value       = aws_db_instance.pdf_rds_instance.username
}

output "db_password" {
  description = "The password for the database."
  value       = aws_db_instance.pdf_rds_instance.password
  sensitive   = true # Mark as sensitive to prevent plaintext logging in Terraform output
}

output "db_port" {
  description = "The port for the database."
  value       = aws_db_instance.pdf_rds_instance.port
}

output "db_subnet_group_name" {
  description = "The name of the DB Subnet Group created."
  value       = aws_db_subnet_group.db_subnet_group.name
}
