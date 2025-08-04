resource "aws_security_group" "app_sg" {
  name        = "app-security-group"
  description = "Security group for application compute resources"
  vpc_id      = var.vpc_id

  # Ingress rule for HTTP/S (if your app is web-facing)
  ingress {
    description = "Allow HTTP access from anywhere"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Allow HTTPS access from anywhere"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Ingress rule for your FastAPI app port (if directly exposed)
  ingress {
    description = "Allow FastAPI app port 8000 from anywhere"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Ingress rule for SSH (if you need to SSH into EC2 instances)
  ingress {
    description = "Allow SSH access from anywhere (consider restricting to specific IPs)"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # IMPORTANT: Restrict this in production to your office/VPN IPs
  }
  ingress {
    description = "Allow SSH access from anywhere (consider restricting to specific IPs)"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # IMPORTANT: Restrict this in production to your office/VPN IPs
  }

  # Egress rule for all outbound traffic (common for applications)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "app-security-group"
  }
}

resource "aws_security_group" "rds_sg" {
  name        = "rds-security-group"
  description = "Security group for RDS PostgreSQL database"
  vpc_id      = var.vpc_id

  # Ingress rule to allow PostgreSQL traffic ONLY from the application security group
  ingress {
    description     = "Allow PostgreSQL from application"
    from_port       = 5432 # PostgreSQL default port
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app_sg.id] # Allow traffic only from the app_sg
  }
  
  # Egress rule for the database (e.g., for outbound connections to S3 for backups, or other AWS services)
  # For a private database, outbound rules can often be more restrictive.
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"] # Or restrict to specific service endpoints
  }

  tags = {
    Name = "rds-security-group"
  }
}

