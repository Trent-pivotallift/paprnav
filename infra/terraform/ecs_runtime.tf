data "aws_iam_policy_document" "ecs_task_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ecs_execution" {
  name               = "${local.name_prefix}-ecs-execution-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role.json
}

resource "aws_iam_role_policy_attachment" "ecs_execution_managed" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

data "aws_iam_policy_document" "ecs_execution_secrets" {
  statement {
    actions = [
      "secretsmanager:GetSecretValue",
    ]

    resources = [
      aws_secretsmanager_secret.database_url.arn,
      aws_secretsmanager_secret.session_secret.arn,
    ]
  }
}

resource "aws_iam_role_policy" "ecs_execution_secrets" {
  name   = "${local.name_prefix}-ecs-execution-secrets"
  role   = aws_iam_role.ecs_execution.id
  policy = data.aws_iam_policy_document.ecs_execution_secrets.json
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

data "aws_iam_policy_document" "api_task" {
  statement {
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:GetObjectTagging",
      "s3:PutObjectTagging",
    ]

    resources = [
      "${aws_s3_bucket.app_artifacts.arn}/*",
    ]
  }

  statement {
    actions = [
      "s3:ListBucket",
    ]

    resources = [
      aws_s3_bucket.app_artifacts.arn,
    ]
  }
}

resource "aws_iam_role_policy" "api_task" {
  name   = "${local.name_prefix}-api-task"
  role   = aws_iam_role.api_task.id
  policy = data.aws_iam_policy_document.api_task.json
}

data "aws_iam_policy_document" "worker_task" {
  statement {
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:GetObjectTagging",
      "s3:PutObjectTagging",
    ]

    resources = [
      "${aws_s3_bucket.app_artifacts.arn}/*",
    ]
  }

  statement {
    actions = [
      "s3:ListBucket",
    ]

    resources = [
      aws_s3_bucket.app_artifacts.arn,
    ]
  }

  statement {
    actions = [
      "textract:DetectDocumentText",
      "textract:StartDocumentTextDetection",
      "textract:GetDocumentTextDetection",
    ]

    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "worker_task" {
  name   = "${local.name_prefix}-worker-task"
  role   = aws_iam_role.worker_task.id
  policy = data.aws_iam_policy_document.worker_task.json
}

locals {
  app_environment_base = [
    { name = "PAPRNAV_ENV", value = var.environment },
    { name = "PAPRNAV_STORAGE_BACKEND", value = "s3" },
    { name = "PAPRNAV_S3_UPLOAD_BUCKET", value = aws_s3_bucket.app_artifacts.bucket },
    { name = "PAPRNAV_S3_UPLOAD_PREFIX", value = "uploads" },
    { name = "AWS_REGION", value = var.aws_region },
  ]

  api_environment = concat(
    local.app_environment_base,
    [
      { name = "PAPRNAV_OCR_PROVIDER", value = "deterministic" },
    ]
  )

  worker_environment = concat(
    local.app_environment_base,
    [
      { name = "PAPRNAV_OCR_PROVIDER", value = "textract" },
    ]
  )

  api_secrets = [
    { name = "DATABASE_URL", valueFrom = aws_secretsmanager_secret.database_url.arn },
    { name = "PAPRNAV_SESSION_SECRET", valueFrom = aws_secretsmanager_secret.session_secret.arn },
  ]
}

resource "aws_ecs_task_definition" "api" {
  family                   = "${local.name_prefix}-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.ecs_task_cpu
  memory                   = var.ecs_task_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.api_task.arn

  container_definitions = jsonencode([
    {
      name      = "api"
      image     = "${aws_ecr_repository.api.repository_url}:latest"
      essential = true

      portMappings = [
        {
          containerPort = var.api_container_port
          hostPort      = var.api_container_port
          protocol      = "tcp"
        }
      ]

      environment = local.api_environment
      secrets     = local.api_secrets

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.api.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "api"
        }
      }
    }
  ])
}

resource "aws_ecs_task_definition" "frontend" {
  family                   = "${local.name_prefix}-frontend"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.ecs_task_cpu
  memory                   = var.ecs_task_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.frontend_task.arn

  container_definitions = jsonencode([
    {
      name      = "frontend"
      image     = "${aws_ecr_repository.frontend.repository_url}:latest"
      essential = true

      portMappings = [
        {
          containerPort = var.frontend_container_port
          hostPort      = var.frontend_container_port
          protocol      = "tcp"
        }
      ]

      environment = [
        { name = "PAPRNAV_ENV", value = var.environment },
        { name = "PAPRNAV_BACKEND_URL", value = "http://${aws_lb.main.dns_name}" },
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.frontend.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "frontend"
        }
      }
    }
  ])
}

resource "aws_ecs_task_definition" "worker" {
  family                   = "${local.name_prefix}-worker"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.ecs_task_cpu
  memory                   = var.ecs_task_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.worker_task.arn

  container_definitions = jsonencode([
    {
      name      = "worker"
      image     = "${aws_ecr_repository.api.repository_url}:latest"
      essential = true
      command   = ["python", "-m", "app.workers.ocr"]

      environment = local.worker_environment
      secrets     = local.api_secrets

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.worker.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "worker"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "api" {
  name            = "${local.name_prefix}-api"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = var.api_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = var.api_container_port
  }

  depends_on = [aws_lb_listener.http]
}

resource "aws_ecs_service" "frontend" {
  name            = "${local.name_prefix}-frontend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.frontend.arn
  desired_count   = var.frontend_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.frontend.arn
    container_name   = "frontend"
    container_port   = var.frontend_container_port
  }

  depends_on = [aws_lb_listener.http]
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
    actions = ["ecs:RunTask"]

    resources = [
      aws_ecs_task_definition.worker.arn,
    ]

    condition {
      test     = "ArnEquals"
      variable = "ecs:cluster"
      values   = [aws_ecs_cluster.main.arn]
    }
  }

  statement {
    actions = ["iam:PassRole"]

    resources = [
      aws_iam_role.ecs_execution.arn,
      aws_iam_role.worker_task.arn,
    ]

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
  name       = "${local.name_prefix}-worker"
  group_name = "default"
  state      = var.worker_schedule_state

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression = var.worker_schedule_expression

  target {
    arn      = aws_ecs_cluster.main.arn
    role_arn = aws_iam_role.worker_scheduler.arn

    ecs_parameters {
      launch_type         = "FARGATE"
      task_definition_arn = aws_ecs_task_definition.worker.arn

      network_configuration {
        subnets          = aws_subnet.public[*].id
        security_groups  = [aws_security_group.ecs_tasks.id]
        assign_public_ip = true
      }
    }
  }
}
