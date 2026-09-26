locals {
  name_prefix = "${var.project}-${var.environment}"

  expected_api_image_prefix       = "${var.aws_account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/${var.project}/${var.environment}-api@sha256:"
  expected_frontend_image_prefix  = "${var.aws_account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/${var.project}/${var.environment}-frontend@sha256:"
  expected_bootstrap_image_prefix = "${var.aws_account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/${var.project}/${var.environment}-bootstrap@sha256:"

  common_tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "terraform"
    Application = "paprnav"
    Owner       = "paprnav"
    CostCenter  = "paprnav"
    DataClass   = "volunteer-logbook-pilot"
  }
}

data "aws_acm_certificate" "pilot" {
  domain      = var.pilot_hostname
  statuses    = ["ISSUED"]
  types       = ["AMAZON_ISSUED"]
  key_types   = ["RSA_2048"]
  tags        = { Project = "paprnav" }
  most_recent = false
}

resource "terraform_data" "certificate_input_gate" {
  input = {
    requested_arn = var.pilot_certificate_arn
    resolved_arn  = data.aws_acm_certificate.pilot.arn
    domain        = data.aws_acm_certificate.pilot.domain
    status        = data.aws_acm_certificate.pilot.status
    project_tag   = lookup(data.aws_acm_certificate.pilot.tags, "Project", "")
  }

  lifecycle {
    precondition {
      condition     = data.aws_acm_certificate.pilot.arn == var.pilot_certificate_arn
      error_message = "The resolved ACM certificate ARN must equal pilot_certificate_arn."
    }

    precondition {
      condition     = data.aws_acm_certificate.pilot.domain == var.pilot_hostname
      error_message = "The resolved ACM certificate primary domain must equal pilot_hostname."
    }

    precondition {
      condition     = data.aws_acm_certificate.pilot.status == "ISSUED"
      error_message = "The resolved ACM certificate must be ISSUED."
    }

    precondition {
      condition     = lookup(data.aws_acm_certificate.pilot.tags, "Project", "") == "paprnav"
      error_message = "The resolved ACM certificate must carry Project=paprnav."
    }

    precondition {
      condition = startswith(
        data.aws_acm_certificate.pilot.arn,
        "arn:aws:acm:${var.aws_region}:${var.aws_account_id}:certificate/"
      )
      error_message = "The resolved ACM certificate ARN must belong to the configured AWS account and region."
    }
  }
}

resource "terraform_data" "deployment_input_gate" {
  input = {
    dns_provider   = "squarespace"
    dns_zone_name  = var.dns_zone_name
    pilot_hostname = var.pilot_hostname
  }

  lifecycle {
    precondition {
      condition = (
        startswith(var.api_image, local.expected_api_image_prefix) &&
        startswith(var.frontend_image, local.expected_frontend_image_prefix) &&
        startswith(var.bootstrap_image, local.expected_bootstrap_image_prefix)
      )
      error_message = "All image digests must reference the exact pilot ECR repository for their task family."
    }

    precondition {
      condition = !var.external_mode || (
        !endswith(var.pilot_hostname, ".invalid") &&
        can(regex("^[^@[:space:]]+@[^@[:space:]]+\\.[^@[:space:]]+$", var.budget_notification_email)) &&
        !endswith(var.budget_notification_email, ".invalid") &&
        can(regex("^arn:aws:iam::[0-9]{12}:(user|role)/.+$", var.policy_updater_principal_arn))
      )
      error_message = "External mode requires a real hostname, budget recipient, and explicit IAM policy-updater principal."
    }

    precondition {
      condition = (
        var.pilot_hostname != lower(trimsuffix(var.dns_zone_name, ".")) &&
        endswith(var.pilot_hostname, ".${lower(trimsuffix(var.dns_zone_name, "."))}")
      )
      error_message = "pilot_hostname must be a subdomain of dns_zone_name so Squarespace can point it to the ALB with a CNAME without replacing the apex website."
    }
  }
}

resource "aws_s3_bucket" "app_artifacts" {
  bucket        = "${local.name_prefix}-artifacts-${var.aws_account_id}"
  force_destroy = var.force_destroy_buckets
}

resource "aws_s3_bucket_public_access_block" "app_artifacts" {
  bucket = aws_s3_bucket.app_artifacts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "app_artifacts" {
  bucket = aws_s3_bucket.app_artifacts.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "app_artifacts" {
  bucket = aws_s3_bucket.app_artifacts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "app_artifacts" {
  bucket = aws_s3_bucket.app_artifacts.id

  rule {
    id     = "retain-current-uploads-expire-old-versions"
    status = "Enabled"

    filter {
      prefix = ""
    }

    noncurrent_version_expiration {
      noncurrent_days = 90
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }

  rule {
    id     = "expire-temporary-derived-artifacts"
    status = "Enabled"

    filter {
      prefix = "tmp/"
    }

    expiration {
      days = 30
    }
  }
}

resource "aws_s3_bucket" "terraform_state" {
  bucket        = "${local.name_prefix}-terraform-state-${var.aws_account_id}"
  force_destroy = false
}

resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_ecr_repository" "api" {
  name                 = "${var.project}/${var.environment}-api"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository" "frontend" {
  name                 = "${var.project}/${var.environment}-frontend"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository" "bootstrap" {
  name                 = "${var.project}/${var.environment}-bootstrap"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_cloudwatch_log_group" "api" {
  name              = "/paprnav/${var.environment}/api"
  retention_in_days = var.log_retention_days
}

resource "aws_cloudwatch_log_group" "frontend" {
  name              = "/paprnav/${var.environment}/frontend"
  retention_in_days = var.log_retention_days
}

resource "aws_cloudwatch_log_group" "worker" {
  name              = "/paprnav/${var.environment}/worker"
  retention_in_days = var.log_retention_days
}

resource "aws_cloudwatch_log_group" "bootstrap" {
  name              = "/paprnav/${var.environment}/bootstrap"
  retention_in_days = var.log_retention_days
}

resource "aws_ecs_cluster" "main" {
  name = local.name_prefix

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_budgets_budget" "monthly_pilot" {
  name         = "${local.name_prefix}-monthly"
  budget_type  = "COST"
  limit_amount = var.budget_limit_usd
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  cost_filter {
    name = "TagKeyValue"
    values = [
      format("user:Project$%s", var.project),
    ]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 50
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.budget_notification_email]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.budget_notification_email]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = [var.budget_notification_email]
  }
}
