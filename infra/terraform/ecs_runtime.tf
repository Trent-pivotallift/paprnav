data "aws_iam_policy_document" "ecs_task_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

locals {
  execution_role_names = toset(["api", "frontend", "worker", "bootstrap"])
  app_environment_base = [
    { name = "PAPRNAV_ENV", value = "pilot" },
    { name = "PAPRNAV_STORAGE_BACKEND", value = "s3" },
    { name = "PAPRNAV_S3_UPLOAD_BUCKET", value = aws_s3_bucket.app_artifacts.bucket },
    { name = "PAPRNAV_S3_UPLOAD_PREFIX", value = "uploads" },
    { name = "PAPRNAV_CORS_ORIGINS", value = "https://${var.pilot_hostname}" },
    { name = "PAPRNAV_SESSION_COOKIE_SECURE", value = "true" },
    { name = "PAPRNAV_AD_V4_ROUTES_ENABLED", value = "false" },
    { name = "PAPRNAV_AD_V4_VALIDATOR2_WRITES_ENABLED", value = "false" },
    { name = "PAPRNAV_AD_V4_SLICE3A_ROUTES_ENABLED", value = "false" },
    { name = "PAPRNAV_AD_V4_SLICE3B_ROUTES_ENABLED", value = "false" },
    { name = "PAPRNAV_AD_V4_SLICE4_READS_ENABLED", value = "false" },
    { name = "PAPRNAV_AD_V4_SLICE4_DRAFTS_ENABLED", value = "false" },
    { name = "PAPRNAV_AD_V4_SLICE4_DECISIONS_ENABLED", value = "false" },
    { name = "AWS_REGION", value = var.aws_region },
  ]
  api_environment = concat(local.app_environment_base, [
    { name = "PAPRNAV_OCR_PROVIDER", value = "deterministic" },
  ])
  worker_environment = concat(local.app_environment_base, [
    { name = "PAPRNAV_OCR_PROVIDER", value = "textract" },
  ])
  api_secrets = [
    { name = "DATABASE_URL", valueFrom = "${aws_secretsmanager_secret.database_url.arn}:DATABASE_URL::" },
    { name = "PAPRNAV_INVITE_SIGNING_SECRET", valueFrom = aws_secretsmanager_secret.invitation_signing.arn },
  ]
  worker_secrets = [
    { name = "DATABASE_URL", valueFrom = "${aws_secretsmanager_secret.database_url.arn}:DATABASE_URL::" },
  ]
  bootstrap_common_environment = [
    { name = "PAPRNAV_ENV", value = "pilot" },
    { name = "PAPRNAV_ADMIN_SECRET_ARN", value = aws_db_instance.postgres.master_user_secret[0].secret_arn },
    { name = "PAPRNAV_DATABASE_HOST", value = aws_db_instance.postgres.address },
    { name = "PAPRNAV_DATABASE_PORT", value = tostring(aws_db_instance.postgres.port) },
    { name = "PAPRNAV_DATABASE_NAME", value = aws_db_instance.postgres.db_name },
    { name = "AWS_REGION", value = var.aws_region },
  ]
}

resource "aws_iam_role" "ecs_execution" {
  for_each           = local.execution_role_names
  name               = "${local.name_prefix}-${each.key}-execution-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role.json
}

resource "aws_iam_role_policy_attachment" "ecs_execution_managed" {
  for_each   = local.execution_role_names
  role       = aws_iam_role.ecs_execution[each.key].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

data "aws_iam_policy_document" "api_execution_secrets" {
  statement {
    actions   = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
    resources = [aws_secretsmanager_secret.database_url.arn, aws_secretsmanager_secret.invitation_signing.arn]
  }
}

resource "aws_iam_role_policy" "api_execution_secrets" {
  name   = "${local.name_prefix}-api-execution-secrets"
  role   = aws_iam_role.ecs_execution["api"].id
  policy = data.aws_iam_policy_document.api_execution_secrets.json
}

data "aws_iam_policy_document" "worker_execution_secrets" {
  statement {
    actions   = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
    resources = [aws_secretsmanager_secret.database_url.arn]
  }
}

resource "aws_iam_role_policy" "worker_execution_secrets" {
  name   = "${local.name_prefix}-worker-execution-secrets"
  role   = aws_iam_role.ecs_execution["worker"].id
  policy = data.aws_iam_policy_document.worker_execution_secrets.json
}

resource "aws_iam_role" "api_task" {
  name               = "${local.name_prefix}-api-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role.json
}

resource "aws_iam_role" "frontend_task" {
  name               = "${local.name_prefix}-frontend-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role.json
}

resource "aws_iam_role" "worker_task" {
  name               = "${local.name_prefix}-worker-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role.json
}

resource "aws_iam_role" "migration_reference_task" {
  name               = "${local.name_prefix}-migration-reference-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role.json
}

resource "aws_iam_role" "runtime_role_task" {
  name               = "${local.name_prefix}-runtime-role-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role.json
}

resource "aws_iam_role" "first_admin_task" {
  name               = "${local.name_prefix}-first-admin-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role.json
}

data "aws_iam_policy_document" "api_task" {
  statement {
    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:GetObjectTagging", "s3:PutObjectTagging"]
    resources = ["${aws_s3_bucket.app_artifacts.arn}/*"]
  }
  statement {
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.app_artifacts.arn]
  }
}

resource "aws_iam_role_policy" "api_task" {
  name   = "${local.name_prefix}-api-task"
  role   = aws_iam_role.api_task.id
  policy = data.aws_iam_policy_document.api_task.json
}

data "aws_iam_policy_document" "worker_task" {
  statement {
    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:GetObjectTagging", "s3:PutObjectTagging"]
    resources = ["${aws_s3_bucket.app_artifacts.arn}/*"]
  }
  statement {
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.app_artifacts.arn]
  }
  statement {
    actions   = ["textract:DetectDocumentText", "textract:StartDocumentTextDetection", "textract:GetDocumentTextDetection"]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "worker_task" {
  name   = "${local.name_prefix}-worker-task"
  role   = aws_iam_role.worker_task.id
  policy = data.aws_iam_policy_document.worker_task.json
}

data "aws_iam_policy_document" "migration_reference_secrets" {
  statement {
    actions   = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
    resources = [aws_db_instance.postgres.master_user_secret[0].secret_arn]
  }
}

resource "aws_iam_role_policy" "migration_reference_secrets" {
  name   = "${local.name_prefix}-migration-reference-secrets"
  role   = aws_iam_role.migration_reference_task.id
  policy = data.aws_iam_policy_document.migration_reference_secrets.json
}

data "aws_iam_policy_document" "runtime_role_secrets" {
  statement {
    actions   = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
    resources = [aws_db_instance.postgres.master_user_secret[0].secret_arn]
  }
  statement {
    actions   = ["secretsmanager:PutSecretValue", "secretsmanager:DescribeSecret"]
    resources = [aws_secretsmanager_secret.database_url.arn]
  }
}

resource "aws_iam_role_policy" "runtime_role_secrets" {
  name   = "${local.name_prefix}-runtime-role-secrets"
  role   = aws_iam_role.runtime_role_task.id
  policy = data.aws_iam_policy_document.runtime_role_secrets.json
}

data "aws_iam_policy_document" "first_admin_secrets" {
  statement {
    actions = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
    resources = [
      aws_db_instance.postgres.master_user_secret[0].secret_arn,
      aws_secretsmanager_secret.first_admin_password.arn,
    ]
  }
}

resource "aws_iam_role_policy" "first_admin_secrets" {
  name   = "${local.name_prefix}-first-admin-secrets"
  role   = aws_iam_role.first_admin_task.id
  policy = data.aws_iam_policy_document.first_admin_secrets.json
}

resource "aws_ecs_task_definition" "api" {
  family                   = "${local.name_prefix}-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.ecs_task_cpu
  memory                   = var.ecs_task_memory
  execution_role_arn       = aws_iam_role.ecs_execution["api"].arn
  task_role_arn            = aws_iam_role.api_task.arn

  container_definitions = jsonencode([{
    name         = "api"
    image        = var.api_image
    essential    = true
    portMappings = [{ containerPort = var.api_container_port, hostPort = var.api_container_port, protocol = "tcp" }]
    environment  = local.api_environment
    secrets      = local.api_secrets
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group = aws_cloudwatch_log_group.api.name, awslogs-region = var.aws_region, awslogs-stream-prefix = "api"
      }
    }
  }])
}

resource "aws_ecs_task_definition" "frontend" {
  family                   = "${local.name_prefix}-frontend"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.ecs_task_cpu
  memory                   = var.ecs_task_memory
  execution_role_arn       = aws_iam_role.ecs_execution["frontend"].arn
  task_role_arn            = aws_iam_role.frontend_task.arn

  container_definitions = jsonencode([{
    name         = "frontend"
    image        = var.frontend_image
    essential    = true
    portMappings = [{ containerPort = var.frontend_container_port, hostPort = var.frontend_container_port, protocol = "tcp" }]
    environment  = [{ name = "PAPRNAV_ENV", value = "pilot" }]
    secrets      = []
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group = aws_cloudwatch_log_group.frontend.name, awslogs-region = var.aws_region, awslogs-stream-prefix = "frontend"
      }
    }
  }])
}

resource "aws_ecs_task_definition" "worker" {
  family                   = "${local.name_prefix}-worker"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.ecs_task_cpu
  memory                   = var.ecs_task_memory
  execution_role_arn       = aws_iam_role.ecs_execution["worker"].arn
  task_role_arn            = aws_iam_role.worker_task.arn

  container_definitions = jsonencode([{
    name        = "worker", image = var.api_image, essential = true, command = ["python", "-m", "app.workers.ocr"]
    environment = local.worker_environment
    secrets     = local.worker_secrets
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group = aws_cloudwatch_log_group.worker.name, awslogs-region = var.aws_region, awslogs-stream-prefix = "worker"
      }
    }
  }])
}

locals {
  bootstrap_tasks = {
    migration = {
      command     = ["migration"]
      role        = aws_iam_role.migration_reference_task.arn
      environment = local.bootstrap_common_environment
    }
    reference = {
      command     = ["reference"]
      role        = aws_iam_role.migration_reference_task.arn
      environment = local.bootstrap_common_environment
    }
    runtime-role = {
      command = ["runtime-role"]
      role    = aws_iam_role.runtime_role_task.arn
      environment = concat(local.bootstrap_common_environment, [
        { name = "PAPRNAV_APP_DATABASE_SECRET_ARN", value = aws_secretsmanager_secret.database_url.arn },
      ])
    }
    first-admin = {
      command = ["first-admin"]
      role    = aws_iam_role.first_admin_task.arn
      environment = concat(local.bootstrap_common_environment, [
        { name = "PAPRNAV_FIRST_ADMIN_SECRET_ARN", value = aws_secretsmanager_secret.first_admin_password.arn },
        { name = "PAPRNAV_FIRST_ADMIN_EMAIL", value = var.first_admin_email },
        { name = "PAPRNAV_FIRST_ADMIN_NAME", value = var.first_admin_name },
        { name = "PAPRNAV_FIRST_ADMIN_ORGANIZATION", value = var.first_admin_organization },
      ])
    }
  }
}

resource "aws_ecs_task_definition" "bootstrap" {
  for_each                 = local.bootstrap_tasks
  family                   = "${local.name_prefix}-bootstrap-${each.key}"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.ecs_task_cpu
  memory                   = var.ecs_task_memory
  execution_role_arn       = aws_iam_role.ecs_execution["bootstrap"].arn
  task_role_arn            = each.value.role

  container_definitions = jsonencode([{
    name                   = "bootstrap"
    image                  = var.bootstrap_image
    essential              = true
    command                = each.value.command
    environment            = each.value.environment
    secrets                = []
    readonlyRootFilesystem = true
    linuxParameters        = { initProcessEnabled = true }
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group = aws_cloudwatch_log_group.bootstrap.name, awslogs-region = var.aws_region, awslogs-stream-prefix = each.key
      }
    }
  }])
}

resource "aws_ecs_service" "api" {
  name            = "${local.name_prefix}-api"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = 0
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.api.id]
    assign_public_ip = true
  }
  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = var.api_container_port
  }
  depends_on = [aws_lb_listener.https]
}

resource "aws_ecs_service" "frontend" {
  name            = "${local.name_prefix}-frontend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.frontend.arn
  desired_count   = 0
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.frontend.id]
    assign_public_ip = true
  }
  load_balancer {
    target_group_arn = aws_lb_target_group.frontend.arn
    container_name   = "frontend"
    container_port   = var.frontend_container_port
  }
  depends_on = [aws_lb_listener.https]
}

data "aws_iam_policy_document" "scheduler_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["scheduler.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "worker_scheduler" {
  name               = "${local.name_prefix}-worker-scheduler-role"
  assume_role_policy = data.aws_iam_policy_document.scheduler_assume_role.json
}

data "aws_iam_policy_document" "worker_scheduler" {
  statement {
    actions   = ["ecs:RunTask"]
    resources = [aws_ecs_task_definition.worker.arn]
    condition {
      test     = "ArnEquals"
      variable = "ecs:cluster"
      values   = [aws_ecs_cluster.main.arn]
    }
  }
  statement {
    actions   = ["iam:PassRole"]
    resources = [aws_iam_role.ecs_execution["worker"].arn, aws_iam_role.worker_task.arn]
    condition {
      test     = "StringEquals"
      variable = "iam:PassedToService"
      values   = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy" "worker_scheduler" {
  name   = "${local.name_prefix}-worker-scheduler"
  role   = aws_iam_role.worker_scheduler.id
  policy = data.aws_iam_policy_document.worker_scheduler.json
}

resource "aws_scheduler_schedule" "worker" {
  name                = "${local.name_prefix}-worker"
  group_name          = "default"
  state               = "DISABLED"
  schedule_expression = "rate(15 minutes)"
  flexible_time_window { mode = "OFF" }

  target {
    arn      = aws_ecs_cluster.main.arn
    role_arn = aws_iam_role.worker_scheduler.arn
    ecs_parameters {
      launch_type         = "FARGATE"
      task_definition_arn = aws_ecs_task_definition.worker.arn
      network_configuration {
        subnets          = aws_subnet.public[*].id
        security_groups  = [aws_security_group.worker.id]
        assign_public_ip = true
      }
    }
  }
}
