variable "region" {
  type = string
}
variable "identifier" {
  type = string
}

variable "instance_class" {
  type = string
}

variable "engine" {
  type = string
}

variable "engine_version" {
  type = string
}

variable "port" {
  type = number
  default = 5432
}

variable "db_username" {
  type = string
}

variable "db_password" {
  type = string
}

variable "db_subnet_ids" {
  type = list(string)
}

variable "database_name" {
  type = string
}

variable "security_group" {
  type = string
}

