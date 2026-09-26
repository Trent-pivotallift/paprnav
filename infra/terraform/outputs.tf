output "app_artifacts_bucket" {
  description = "S3 bucket for uploaded logbooks and derived OCR artifacts."
  value       = aws_s3_bucket.app_artifacts.bucket
}

output "terraform_state_bucket" {
  description = "S3 bucket prepared for Terraform state migration."
  value       = aws_s3_bucket.terraform_state.bucket
}

output "api_ecr_repository_url" {
  description = "ECR repository URL for the FastAPI backend image."
  value       = aws_ecr_repository.api.repository_url
}

output "frontend_ecr_repository_url" {
  description = "ECR repository URL for the Next.js frontend image."
  value       = aws_ecr_repository.frontend.repository_url
}

output "bootstrap_ecr_repository_url" {
  description = "ECR repository URL for the sealed migration/bootstrap image."
  value       = aws_ecr_repository.bootstrap.repository_url
}

output "ecs_cluster_name" {
  description = "ECS cluster name for paprnav pilot services."
  value       = aws_ecs_cluster.main.name
}

output "vpc_id" {
  description = "VPC ID for the paprnav pilot runtime skeleton."
  value       = aws_vpc.main.id
}

output "alb_dns_name" {
  description = "Public ALB DNS name behind the canonical HTTPS pilot record."
  value       = aws_lb.main.dns_name
}

output "pilot_dns_cname" {
  description = "Manual DNS handoff for the Squarespace-managed pilot hostname."
  value = {
    provider    = "Squarespace"
    name        = var.pilot_hostname
    type        = "CNAME"
    value       = aws_lb.main.dns_name
    ttl_seconds = 300
  }
}

output "pilot_https_url" {
  description = "Canonical HTTPS URL."
  value       = "https://${var.pilot_hostname}"
}

output "pilot_certificate_arn" {
  description = "Verified operator-provisioned ACM certificate attached to the HTTPS listener."
  value       = data.aws_acm_certificate.pilot.arn
}

output "api_service_name" {
  description = "ECS API service name."
  value       = aws_ecs_service.api.name
}

output "frontend_service_name" {
  description = "ECS frontend service name."
  value       = aws_ecs_service.frontend.name
}

output "api_task_definition_arn" {
  description = "API task definition ARN."
  value       = aws_ecs_task_definition.api.arn
}

output "frontend_task_definition_arn" {
  description = "Frontend task definition ARN."
  value       = aws_ecs_task_definition.frontend.arn
}

output "worker_task_definition_arn" {
  description = "Worker task definition ARN."
  value       = aws_ecs_task_definition.worker.arn
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint."
  value       = aws_db_instance.postgres.endpoint
}

output "rds_master_user_secret_arn" {
  description = "AWS-managed RDS master user secret ARN."
  value       = aws_db_instance.postgres.master_user_secret[0].secret_arn
}

output "database_url_secret_arn" {
  description = "Secret ARN for app DATABASE_URL. Populate before starting ECS tasks."
  value       = aws_secretsmanager_secret.database_url.arn
}

output "invitation_signing_secret_arn" {
  description = "Secret ARN for the dedicated invitation-signing secret."
  value       = aws_secretsmanager_secret.invitation_signing.arn
}

output "first_admin_password_secret_arn" {
  description = "One-use first-administrator password secret ARN."
  value       = aws_secretsmanager_secret.first_admin_password.arn
}

output "worker_schedule_name" {
  description = "EventBridge Scheduler schedule for the OCR worker task."
  value       = aws_scheduler_schedule.worker.name
}

output "bootstrap_task_definition_arns" {
  description = "Fixed one-off task definitions; running them remains a Package E gate."
  value       = { for phase, task in aws_ecs_task_definition.bootstrap : phase => task.arn }
}
