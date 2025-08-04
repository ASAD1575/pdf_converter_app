provider "aws" {
  region = var.region
}

resource "aws_db_subnet_group" "db_subnet_group" {
  name       = "rds-subnet-group"
  subnet_ids = var.db_subnet_ids
  tags = {
    Name = "rds-subnet-group"
  }
}

resource "aws_db_instance" "pdf_rds_instance" {
  identifier              = var.identifier
  instance_class          = var.instance_class
  engine                  = var.engine
  engine_version          = var.engine_version
  port                    = var.port
  username                = var.db_username
  password                = var.db_password
  db_name                 = var.database_name
  allocated_storage       = 20
  skip_final_snapshot     = true
  db_subnet_group_name    = aws_db_subnet_group.db_subnet_group.name
  vpc_security_group_ids  = [ var.security_group ]
  publicly_accessible     = false
  multi_az                = false
  storage_encrypted       = false
  tags = {
    Name = "pdf-database"
  }
}
