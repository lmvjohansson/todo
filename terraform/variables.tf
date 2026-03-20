variable "aws_region" {
  description = "AWS region to deploy resources in"
  type        = string
  default     = "eu-north-1"
}

variable "rds_database_name" {
  description = "AWS RDS database name"
  type        = string
  default     = "todo_db"
}

variable "rds_endpoint" {
  description = "AWS RDS endpoint"
  type        = string
  default     = "todo-db.c9is82wio6qa.eu-north-1.rds.amazonaws.com"
}

variable "rds_secret" {
  description = "AWS RDS secret"
  type        = string
  default     = "rds!db-5e02dc49-6e8e-462a-914f-a75209c78278"
}