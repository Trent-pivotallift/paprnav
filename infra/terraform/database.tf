resource "aws_db_subnet_group" "main" {
  name       = local.name_prefix
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = local.name_prefix
  }
}

resource "aws_db_instance" "postgres" {
  identifier = local.name_prefix

  engine         = "postgres"
  engine_version = var.db_engine_version
  instance_class = var.db_instance_class

  allocated_storage     = var.db_allocated_storage_gb
  max_allocated_storage = max(var.db_allocated_storage_gb, 100)
  storage_encrypted     = true
  storage_type          = "gp3"

  db_name                     = "paprnav"
  username                    = "paprnav_app"
  manage_master_user_password = true

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false

  backup_retention_period = var.db_backup_retention_days
  deletion_protection     = var.rds_deletion_protection
  skip_final_snapshot     = false
  final_snapshot_identifier = replace(
    "${local.name_prefix}-final-${formatdate("YYYYMMDDhhmmss", timestamp())}",
    "/[^A-Za-z0-9-]/",
    "-"
  )

  lifecycle {
    ignore_changes = [final_snapshot_identifier]
  }

  tags = {
    Name = local.name_prefix
  }
}

resource "aws_secretsmanager_secret" "database_url" {
  name        = "/${var.project}/${var.environment}/database-url"
  description = "SQLAlchemy DATABASE_URL for the paprnav pilot API and worker. Populate after RDS creation."
}

resource "aws_secretsmanager_secret" "session_secret" {
  name        = "/${var.project}/${var.environment}/session-secret"
  description = "Application session secret for the paprnav pilot runtime. Populate before starting ECS tasks."
}
