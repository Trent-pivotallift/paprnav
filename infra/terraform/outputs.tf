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

output "ecs_cluster_name" {
  description = "ECS cluster name for paprnav pilot services."
  value       = aws_ecs_cluster.main.name
}

output "vpc_id" {
  description = "VPC ID for the paprnav pilot runtime skeleton."
  value       = aws_vpc.main.id
}

output "alb_dns_name" {
  description = "Public ALB DNS name for the HTTP pilot runtime skeleton."
  value       = aws_lb.main.dns_name
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

output "session_secret_arn" {
  description = "Secret ARN for the app session secret. Populate before starting ECS tasks."
  value       = aws_secretsmanager_secret.session_secret.arn
}

output "worker_schedule_name" {
  description = "EventBridge Scheduler schedule for the OCR worker task."
  value       = aws_scheduler_schedule.worker.name
}
