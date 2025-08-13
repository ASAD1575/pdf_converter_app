output "name" {
  description = "The name of the EFS file system."
  value       = aws_efs_file_system.libreoffice_fs.name
  
}

output "LibreOfficeEFS_access_point" {
  description = "The access point ID for the EFS file system."
  value       = aws_efs_access_point.libreoffice_ap.id
  
}

output "file_system_dns" {
  description = "The DNS name of the EFS file system."
  value       = aws_efs_file_system.libreoffice_fs.dns_name
  
}

output "efs_access_point_arn" {
  value = aws_efs_access_point.libreoffice_ap.arn
  description = "The ARN of the EFS access point."
}