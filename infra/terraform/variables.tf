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
  type    = string
  default = "paprnav"
}

variable "environment" {
  type    = string
  default = "pilot"
}

variable "external_mode" {
  description = "Enable execution-ready input checks. Package C fixture plans keep this false."
  type        = bool
  default     = false
}

variable "pilot_hostname" {
  description = "Operator-owned canonical hostname; no default is permitted."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)+$", var.pilot_hostname))
    error_message = "pilot_hostname must be one canonical lower-case DNS hostname."
  }
}

variable "pilot_certificate_arn" {
  description = "Exact ARN of the operator-provisioned, issued ACM certificate for pilot_hostname."
  type        = string

  validation {
    condition     = can(regex("^arn:aws:acm:[a-z0-9-]+:[0-9]{12}:certificate/[0-9a-f-]+$", var.pilot_certificate_arn))
    error_message = "pilot_certificate_arn must be one exact ACM certificate ARN."
  }
}

variable "dns_zone_name" {
  description = "Squarespace-managed DNS zone containing pilot_hostname. Terraform never reads or changes this zone."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)+$", var.dns_zone_name))
    error_message = "dns_zone_name must be one canonical lower-case DNS zone name without a trailing dot."
  }
}

variable "budget_notification_email" {
  description = "Real AWS Budget recipient in external mode; no repository default."
  type        = string
}

variable "policy_updater_principal_arn" {
  description = "Operator-admin principal authorized to version only paprnav-terraform-deploy."
  type        = string
}

variable "api_image" {
  description = "Immutable API image reference."
  type        = string

  validation {
    condition     = can(regex("^[^:@[:space:]]+(?::[0-9]+)?/[^:@[:space:]]+@sha256:[0-9a-f]{64}$", var.api_image))
    error_message = "api_image must be a repository@sha256:<64 lowercase hex> reference."
  }
}

variable "frontend_image" {
  description = "Immutable frontend image reference."
  type        = string

  validation {
    condition     = can(regex("^[^:@[:space:]]+(?::[0-9]+)?/[^:@[:space:]]+@sha256:[0-9a-f]{64}$", var.frontend_image))
    error_message = "frontend_image must be a repository@sha256:<64 lowercase hex> reference."
  }
}

variable "bootstrap_image" {
  description = "Immutable dedicated migration/bootstrap image reference."
  type        = string

  validation {
    condition     = can(regex("^[^:@[:space:]]+(?::[0-9]+)?/[^:@[:space:]]+@sha256:[0-9a-f]{64}$", var.bootstrap_image))
    error_message = "bootstrap_image must be a repository@sha256:<64 lowercase hex> reference."
  }
}

variable "first_admin_email" {
  description = "First administrator identity; the password remains only in Secrets Manager."
  type        = string
}

variable "first_admin_name" {
  description = "First administrator display name."
  type        = string
}

variable "first_admin_organization" {
  description = "Permanent platform organization name created during first-admin bootstrap."
  type        = string
}

variable "budget_limit_usd" {
  type    = string
  default = "300"
}

variable "log_retention_days" {
  type    = number
  default = 30
}

variable "force_destroy_buckets" {
  description = "Must remain false for volunteer-data safety."
  type        = bool
  default     = false

  validation {
    condition     = !var.force_destroy_buckets
    error_message = "pilot buckets may not use force_destroy."
  }
}

variable "vpc_cidr" {
  type    = string
  default = "10.42.0.0/16"
}

variable "public_subnet_cidrs" {
  type    = list(string)
  default = ["10.42.0.0/24", "10.42.1.0/24"]
}

variable "private_subnet_cidrs" {
  type    = list(string)
  default = ["10.42.10.0/24", "10.42.11.0/24"]
}

variable "api_container_port" {
  type    = number
  default = 8000
}

variable "frontend_container_port" {
  type    = number
  default = 3000
}

variable "ecs_task_cpu" {
  type    = number
  default = 512
}

variable "ecs_task_memory" {
  type    = number
  default = 1024
}

variable "db_instance_class" {
  type    = string
  default = "db.t4g.micro"
}

variable "db_allocated_storage_gb" {
  type    = number
  default = 20
}

variable "db_engine_version" {
  type    = string
  default = "16.3"
}

variable "db_backup_retention_days" {
  type    = number
  default = 7
}

variable "rds_deletion_protection" {
  type    = bool
  default = true

  validation {
    condition     = var.rds_deletion_protection
    error_message = "pilot RDS deletion protection must remain enabled."
  }
}

variable "login_rate_limit" {
  description = "Five-minute per-IP login request threshold."
  type        = number
  default     = 100
}

variable "invitation_rate_limit" {
  description = "Five-minute per-IP invitation create/accept threshold."
  type        = number
  default     = 50
}
