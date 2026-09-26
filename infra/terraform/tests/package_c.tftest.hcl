mock_provider "aws" {
  mock_data "aws_availability_zones" {
    defaults = {
      names = ["us-east-1a", "us-east-1b"]
    }
  }

  # Targeting the bootstrap task definitions also plans their IAM role
  # dependencies. Keep every mocked policy document valid at plan time so
  # provider schema validation cannot obscure the container assertions.
  mock_data "aws_iam_policy_document" {
    defaults = {
      json = "{\"Version\":\"2012-10-17\",\"Statement\":[]}"
    }
  }

  mock_data "aws_acm_certificate" {
    defaults = {
      arn    = "arn:aws:acm:us-east-1:527257972989:certificate/11111111-2222-3333-4444-555555555555"
      domain = "pilot.example.com"
      status = "ISSUED"
      tags   = { Project = "paprnav" }
    }
  }
}

variables {
  pilot_hostname               = "pilot.example.com"
  pilot_certificate_arn        = "arn:aws:acm:us-east-1:527257972989:certificate/11111111-2222-3333-4444-555555555555"
  dns_zone_name                = "example.com"
  budget_notification_email    = "pilot-owner@example.com"
  policy_updater_principal_arn = "arn:aws:iam::527257972989:role/paprnav-policy-updater"
  api_image                    = "527257972989.dkr.ecr.us-east-1.amazonaws.com/paprnav/pilot-api@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  frontend_image               = "527257972989.dkr.ecr.us-east-1.amazonaws.com/paprnav/pilot-frontend@sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
  bootstrap_image              = "527257972989.dkr.ecr.us-east-1.amazonaws.com/paprnav/pilot-bootstrap@sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
  first_admin_email            = "first-admin@example.com"
  first_admin_name             = "First Admin"
  first_admin_organization     = "Paprnav"
}

run "valid_gate_inputs" {
  command = plan

  plan_options {
    target = [terraform_data.deployment_input_gate]
  }
}

run "valid_certificate_gate" {
  command = plan

  plan_options {
    target = [terraform_data.certificate_input_gate]
  }

  assert {
    condition = (
      data.aws_acm_certificate.pilot.domain == var.pilot_hostname &&
      data.aws_acm_certificate.pilot.most_recent == false &&
      length(data.aws_acm_certificate.pilot.statuses) == 1 &&
      data.aws_acm_certificate.pilot.statuses[0] == "ISSUED" &&
      length(data.aws_acm_certificate.pilot.types) == 1 &&
      data.aws_acm_certificate.pilot.types[0] == "AMAZON_ISSUED" &&
      length(data.aws_acm_certificate.pilot.key_types) == 1 &&
      contains(data.aws_acm_certificate.pilot.key_types, "RSA_2048") &&
      length(data.aws_acm_certificate.pilot.tags) == 1 &&
      lookup(data.aws_acm_certificate.pilot.tags, "Project", "") == "paprnav"
    )
    error_message = "The ACM lookup must remain exact, issued, Amazon-issued, RSA_2048, Project-owned, and ambiguity rejecting."
  }
}

run "bootstrap_database_location_is_bound_to_rds" {
  command = plan

  # The assertions decode container_definitions during planning, so every
  # resource-derived value in that JSON must be known before apply.
  override_resource {
    target          = aws_db_instance.postgres
    override_during = plan
    values = {
      address = "paprnav-bootstrap-plan.invalid"
      port    = 5432
      db_name = "paprnav"
      master_user_secret = [{
        secret_arn = "arn:aws:secretsmanager:us-east-1:527257972989:secret:rds!db-package-c-plan"
      }]
    }
  }

  override_resource {
    target          = aws_secretsmanager_secret.database_url
    override_during = plan
    values = {
      arn = "arn:aws:secretsmanager:us-east-1:527257972989:secret:paprnav/package-c/app-database-plan-000001"
    }
  }

  override_resource {
    target          = aws_secretsmanager_secret.first_admin_password
    override_during = plan
    values = {
      arn = "arn:aws:secretsmanager:us-east-1:527257972989:secret:paprnav/package-c/first-admin-plan-000001"
    }
  }

  override_resource {
    target          = aws_cloudwatch_log_group.bootstrap
    override_during = plan
    values = {
      name = "/paprnav/package-c/bootstrap-plan"
    }
  }

  plan_options {
    target = [aws_ecs_task_definition.bootstrap]
  }

  assert {
    condition = alltrue([
      for phase, task in aws_ecs_task_definition.bootstrap : (
        lookup({
          for item in jsondecode(task.container_definitions)[0].environment : item.name => item.value
        }, "PAPRNAV_DATABASE_HOST", "") == aws_db_instance.postgres.address &&
        lookup({
          for item in jsondecode(task.container_definitions)[0].environment : item.name => item.value
        }, "PAPRNAV_DATABASE_PORT", "") == tostring(aws_db_instance.postgres.port)
      )
    ])
    error_message = "Every sealed bootstrap task must bind its host and port directly to the Terraform-managed RDS instance."
  }

  assert {
    condition = alltrue([
      for phase, task in aws_ecs_task_definition.bootstrap : (
        length(jsondecode(task.container_definitions)[0].command) == 1 &&
        jsondecode(task.container_definitions)[0].command[0] == phase
      )
    ])
    error_message = "Each bootstrap task definition must retain its one fixed phase command."
  }
}

run "wrong_certificate_arn_is_blocked" {
  command = plan

  variables {
    pilot_certificate_arn = "arn:aws:acm:us-east-1:527257972989:certificate/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
  }

  plan_options {
    target = [terraform_data.certificate_input_gate]
  }

  expect_failures = [terraform_data.certificate_input_gate]
}

run "wrong_certificate_domain_is_blocked" {
  command = plan

  override_data {
    target = data.aws_acm_certificate.pilot
    values = { domain = "unrelated.example.net" }
  }

  plan_options {
    target = [terraform_data.certificate_input_gate]
  }

  expect_failures = [terraform_data.certificate_input_gate]
}

run "wrong_certificate_status_is_blocked" {
  command = plan

  override_data {
    target = data.aws_acm_certificate.pilot
    values = { status = "PENDING_VALIDATION" }
  }

  plan_options {
    target = [terraform_data.certificate_input_gate]
  }

  expect_failures = [terraform_data.certificate_input_gate]
}

run "wrong_certificate_tag_is_blocked" {
  command = plan

  override_data {
    target = data.aws_acm_certificate.pilot
    values = { tags = { Project = "other" } }
  }

  plan_options {
    target = [terraform_data.certificate_input_gate]
  }

  expect_failures = [terraform_data.certificate_input_gate]
}

run "wrong_certificate_account_is_blocked" {
  command = plan

  variables {
    pilot_certificate_arn = "arn:aws:acm:us-east-1:111111111111:certificate/11111111-2222-3333-4444-555555555555"
  }

  override_data {
    target = data.aws_acm_certificate.pilot
    values = { arn = "arn:aws:acm:us-east-1:111111111111:certificate/11111111-2222-3333-4444-555555555555" }
  }

  plan_options {
    target = [terraform_data.certificate_input_gate]
  }

  expect_failures = [terraform_data.certificate_input_gate]
}

run "wrong_certificate_region_is_blocked" {
  command = plan

  variables {
    pilot_certificate_arn = "arn:aws:acm:us-west-2:527257972989:certificate/11111111-2222-3333-4444-555555555555"
  }

  override_data {
    target = data.aws_acm_certificate.pilot
    values = { arn = "arn:aws:acm:us-west-2:527257972989:certificate/11111111-2222-3333-4444-555555555555" }
  }

  plan_options {
    target = [terraform_data.certificate_input_gate]
  }

  expect_failures = [terraform_data.certificate_input_gate]
}

# Export this plan with `terraform test -json -verbose` for the bounded Python
# request oracle in test_pilot_package_c.py. Only computed ARNs are mocked; the
# WAF statements, field selectors, transformations and regexes are real config.
run "waf_auth_and_upload_contract" {
  command = plan

  override_resource {
    target          = aws_wafv2_regex_pattern_set.login_path
    override_during = plan
    values = {
      arn = "arn:aws:wafv2:us-east-1:527257972989:regional/regexpatternset/paprnav-login/11111111-1111-1111-1111-111111111111"
    }
  }
  override_resource {
    target          = aws_wafv2_regex_pattern_set.invitation_paths
    override_during = plan
    values = {
      arn = "arn:aws:wafv2:us-east-1:527257972989:regional/regexpatternset/paprnav-invitation/22222222-2222-2222-2222-222222222222"
    }
  }
  override_resource {
    target          = aws_wafv2_regex_pattern_set.upload_path
    override_during = plan
    values = {
      arn = "arn:aws:wafv2:us-east-1:527257972989:regional/regexpatternset/paprnav-upload/33333333-3333-3333-3333-333333333333"
    }
  }

  plan_options {
    target = [aws_wafv2_web_acl.pilot]
  }

  assert {
    condition = length([
      for rule in aws_wafv2_web_acl.pilot.rule : rule
      if contains(["login-rate-limit", "invitation-rate-limit"], rule.name)
      ]) == 2 && alltrue(flatten([
        for rule in aws_wafv2_web_acl.pilot.rule : [
          for predicate in one(one(rule.statement).rate_based_statement).scope_down_statement[0].and_statement[0].statement : (
            length(predicate.byte_match_statement) == 1 ? (
              one(predicate.byte_match_statement).search_string == "POST" &&
              one(predicate.byte_match_statement).positional_constraint == "EXACTLY" &&
              length(one(predicate.byte_match_statement).field_to_match[0].method) == 1 &&
              one(one(predicate.byte_match_statement).text_transformation).type == "NONE"
              ) : (
              length(one(predicate.regex_pattern_set_reference_statement).field_to_match[0].uri_path) == 1 &&
              one(one(predicate.regex_pattern_set_reference_statement).text_transformation).type == "URL_DECODE"
            )
          )
        ] if contains(["login-rate-limit", "invitation-rate-limit"], rule.name)
    ]))
    error_message = "Both auth rules must match raw POST methods and URL_DECODE the URI predicate itself."
  }

  assert {
    condition = alltrue(concat(
      [for visibility in aws_wafv2_web_acl.pilot.visibility_config : !visibility.sampled_requests_enabled],
      flatten([for rule in aws_wafv2_web_acl.pilot.rule : [
        for visibility in rule.visibility_config : !visibility.sampled_requests_enabled
      ]])
    ))
    error_message = "No WAF sampling may retain session-bearing requests."
  }
}

run "wrong_api_repository_is_blocked" {
  command = plan

  variables {
    api_image = "527257972989.dkr.ecr.us-east-1.amazonaws.com/unrelated/api@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  }

  plan_options {
    target = [terraform_data.deployment_input_gate]
  }

  expect_failures = [terraform_data.deployment_input_gate]
}

run "wrong_external_dns_zone_identity_is_blocked" {
  command = plan

  variables {
    dns_zone_name = "unrelated.example.net"
  }

  plan_options {
    target = [terraform_data.deployment_input_gate]
  }

  expect_failures = [terraform_data.deployment_input_gate]
}

run "external_dns_handoff_is_cname_to_alb" {
  command = plan

  override_resource {
    target          = aws_lb.main
    override_during = plan
    values = {
      dns_name = "paprnav-pilot-123456789.us-east-1.elb.amazonaws.com"
    }
  }

  plan_options {
    target = [aws_lb.main]
  }

  assert {
    condition = (
      output.pilot_dns_cname.provider == "Squarespace" &&
      output.pilot_dns_cname.name == var.pilot_hostname &&
      output.pilot_dns_cname.type == "CNAME" &&
      output.pilot_dns_cname.value == "paprnav-pilot-123456789.us-east-1.elb.amazonaws.com" &&
      output.pilot_dns_cname.ttl_seconds == 300
    )
    error_message = "The external DNS handoff must direct the pilot hostname to the Terraform-managed ALB with a Squarespace CNAME."
  }
}

run "placeholder_external_input_is_blocked" {
  command = plan

  variables {
    external_mode             = true
    budget_notification_email = "owner@example.invalid"
  }

  plan_options {
    target = [terraform_data.deployment_input_gate]
  }

  expect_failures = [terraform_data.deployment_input_gate]
}
