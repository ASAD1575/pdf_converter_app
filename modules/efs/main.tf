provider "aws" {
  region = var.region
}

resource "aws_efs_file_system" "libreoffice_fs" {
  creation_token = var.efs_name
  performance_mode = "generalPurpose"
  throughput_mode = "bursting"
  encrypted = true
  lifecycle_policy {
    transition_to_ia = "AFTER_30_DAYS"
  }
  tags = {
    Name = var.efs_name
  }
}

resource "aws_efs_access_point" "libreoffice_ap" {
  file_system_id = aws_efs_file_system.libreoffice_fs.id
  posix_user {
    uid = 1000
    gid = 1000
  }
  root_directory {
    path = "/"
    creation_info {
      owner_uid = 1000
      owner_gid = 1000
      permissions = "777"
    }
  }
  tags = {
    Name = "${var.efs_name}-access-point"
  }
  
}

resource "aws_efs_mount_target" "libreoffice_mount_target" {
  for_each        = toset(var.subnet_ids)
  file_system_id = aws_efs_file_system.libreoffice_fs.id
  subnet_id      = each.value
  security_groups = [var.security_group_id]
}

