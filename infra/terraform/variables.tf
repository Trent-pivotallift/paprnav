variable "aws_account_id" {
  description = "AWS account allowed for paprnav pilot deployment."
  type        = string
  default     = "527257972989"
}

variable "aws_region" {
  description = "AWS region for the paprnav pilot."
  type        = string
  default     = "us-east-1"
}

variable "aws_profile" {
  description = "Local AWS CLI profile that assumes the paprnav deployment role."
  type        = string
  default     = "paprnav-deploy"
}

variable "project" {
  description = "Project tag and resource prefix."
  type        = string
  default     = "paprnav"
}

variable "environment" {
  description = "Deployment environment."
  type        = string
  default     = "pilot"
}

variable "budget_limit_usd" {
  description = "Monthly pilot budget limit in USD."
  type        = string
  default     = "300"
}

variable "budget_notification_email" {
  description = "Email address for AWS budget notifications. Empty disables budget notifications and should only be used for local planning."
  type        = string
  default     = ""
}

variable "log_retention_days" {
  description = "CloudWatch log retention for pilot services."
  type        = number
  default     = 30
}

variable "force_destroy_buckets" {
  description = "Allow Terraform to destroy non-empty pilot buckets. Keep false for volunteer data safety."
  type        = bool
  default     = false
}

variable "vpc_cidr" {
  description = "CIDR block for the paprnav pilot VPC."
  type        = string
  default     = "10.42.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public ALB/ECS subnets."
  type        = list(string)
  default     = ["10.42.0.0/24", "10.42.1.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private database subnets."
  type        = list(string)
  default     = ["10.42.10.0/24", "10.42.11.0/24"]
}

variable "api_container_port" {
  description = "Container port for the FastAPI service."
  type        = number
  default     = 8000
}

variable "frontend_container_port" {
  description = "Container port for the Next.js frontend service."
  type        = number
  default     = 3000
}

variable "api_desired_count" {
  description = "Desired ECS task count for the API service. Keep 0 until the API image is pushed."
  type        = number
  default     = 0
}

variable "frontend_desired_count" {
  description = "Desired ECS task count for the frontend service. Keep 0 until the frontend image is pushed."
  type        = number
  default     = 0
}

variable "ecs_task_cpu" {
  description = "Default Fargate task CPU units for pilot API/frontend tasks."
  type        = number
  default     = 512
}

variable "ecs_task_memory" {
  description = "Default Fargate task memory in MiB for pilot API/frontend tasks."
  type        = number
  default     = 1024
}

variable "db_instance_class" {
  description = "RDS PostgreSQL instance class for the pilot."
  type        = string
  default     = "db.t4g.micro"
}

variable "db_allocated_storage_gb" {
  description = "Allocated RDS PostgreSQL storage in GiB."
  type        = number
  default     = 20
}

variable "db_engine_version" {
  description = "RDS PostgreSQL engine version."
  type        = string
  default     = "16.3"
}

variable "db_backup_retention_days" {
  description = "RDS automated backup retention in days."
  type        = number
  default     = 7
}

variable "rds_deletion_protection" {
  description = "Enable deletion protection for the pilot RDS instance."
  type        = bool
  default     = true
}

variable "worker_schedule_expression" {
  description = "EventBridge Scheduler expression for the OCR worker task."
  type        = string
  default     = "rate(15 minutes)"
}

variable "worker_schedule_state" {
  description = "EventBridge Scheduler state for the OCR worker task. Keep DISABLED until images and secrets are ready."
  type        = string
  default     = "DISABLED"

  validation {
    condition     = contains(["ENABLED", "DISABLED"], var.worker_schedule_state)
    error_message = "worker_schedule_state must be ENABLED or DISABLED."
  }
}
