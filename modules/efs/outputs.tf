output "name" {
  description = "The name of the EFS file system."
  value       = aws_efs_file_system.libreoffice_fs.name
  
}

output "LibreOfficeEFS_access_point" {
  description = "The access point ID for the EFS file system."
  value       = aws_efs_access_point.libreoffice_ap.arn
  
}

output "file_system_dns" {
  description = "The DNS name of the EFS file system."
  value       = aws_efs_file_system.libreoffice_fs.dns_name
  
}
