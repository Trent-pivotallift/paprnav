#!/usr/bin/env python3
"""Offline IAM decision authority. No AWS client, credentials, or mutation mode.

This is a deliberately closed evaluator for this graph and provider 5.100.0,
not an IAM simulator. Unsupported policy syntax, source drift and incomplete
evidence stop. Live IAM/SCP/session simulation and M1/M6 approval remain required.
"""
from __future__ import annotations

import argparse
from functools import lru_cache
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import subprocess
from typing import Any
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ACCOUNT = "527257972989"
REGION = "us-east-1"
ROLE = f"arn:aws:iam::{ACCOUNT}:role/paprnav-terraform-deploy"
POLICY = f"arn:aws:iam::{ACCOUNT}:policy/paprnav-terraform-deploy-pilot-supplement"
SECRET_NAMES = {
    "aws_secretsmanager_secret.database_url": "/paprnav/pilot/database-url",
    "aws_secretsmanager_secret.invitation_signing": "/paprnav/pilot/invitation-signing",
    "aws_secretsmanager_secret.first_admin_password": "/paprnav/pilot/first-admin-password",
}
EXCLUDED = ("secretsmanager:UpdateSecret", "secretsmanager:GetSecretValue", "secretsmanager:PutSecretValue")
GENERATOR_SHA256 = "008f8b5c3ae73b89c09337efb31e3919b4c22d968c36a820f2c85e61de5a9b33"
BASELINE_SHA256 = "dc7e543afbd7b42f459118591499e9d11f7b5b1be29f8a93e2bf22a8f722083d"


class Stop(ValueError):
    """Insufficient or incompatible evidence; do not execute."""


def require(ok: Any, reason: str) -> None:
    if not ok:
        raise Stop(reason)


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def many(value: Any) -> list:
    return value if isinstance(value, list) else [value]


def iam_match(pattern: str, value: str) -> bool:
    """IAM glob syntax: only '*' and '?' are metacharacters, never [] classes."""
    return re.fullmatch("".join(".*" if c == "*" else "." if c == "?" else re.escape(c) for c in pattern), value, re.S) is not None


def epsilon(pattern: str, states: frozenset[int]) -> frozenset[int]:
    result = set(states)
    pending = list(states)
    while pending:
        i = pending.pop()
        if i < len(pattern) and pattern[i] == "*" and i + 1 not in result:
            result.add(i + 1)
            pending.append(i + 1)
    return frozenset(result)


def advance(pattern: str, states: frozenset[int], char: str | None) -> frozenset[int]:
    return epsilon(pattern, frozenset(
        i if pattern[i] == "*" else i + 1 for i in states if i < len(pattern)
        and (pattern[i] in {"*", "?"} or pattern[i] == char)
    ))


@lru_cache(maxsize=8192)
def pattern_relation(left: str, right: str, inclusion: bool) -> bool:
    """Product automaton: right subset of left, or nonempty intersection.

    Literal characters plus one OTHER transition partition the entire alphabet.
    This proves every suffix rather than probing a finite set of example ARNs.
    """
    alphabet = set(left + right) - {"*", "?"}
    alphabet.add(None)
    pending = [(epsilon(left, frozenset({0})), epsilon(right, frozenset({0})))]
    seen = set()
    while pending:
        a, b = pending.pop()
        if (a, b) in seen:
            continue
        seen.add((a, b))
        if len(right) in b:
            if inclusion and len(left) not in a:
                return False
            if not inclusion and len(left) in a:
                return True
        for char in alphabet:
            aa, bb = advance(left, a, char), advance(right, b, char)
            if bb and (inclusion or aa):
                pending.append((aa, bb))
    return inclusion


def resource_covers(grant: str, resource: str) -> bool:
    return pattern_relation(grant, resource, True)


def forbidden_secret_overlap(policies: list[dict]) -> None:
    domain = f"arn:aws:secretsmanager:{REGION}:{ACCOUNT}:secret:/paprnav/pilot/*"
    for policy in policies:
        for stmt in policy["Statement"]:
            if stmt["Effect"] == "Allow" and any(iam_match(pattern.lower(), action.lower()) for pattern in many(stmt["Action"]) for action in EXCLUDED):
                # A conditional grant is still a possible grant. Do not infer
                # impossibility from one request context or a compensating Deny.
                require(not any(pattern_relation(scope, domain, False) for scope in many(stmt["Resource"])), "possible forbidden secret-domain grant")


def policy_contract(generated: dict, baseline: dict, root: Path = ROOT) -> None:
    path = root / "scripts/generate_pilot_deploy_policy.py"
    require(hashlib.sha256(path.read_bytes()).hexdigest() == GENERATOR_SHA256, "policy construction source drift")
    # Historical compact baseline hash uses insertion order, intentionally
    # matching the retained immutable document evidence.
    require(hashlib.sha256(json.dumps(baseline, separators=(",", ":")).encode()).hexdigest() == BASELINE_SHA256, "baseline policy drift")
    spec = importlib.util.spec_from_file_location("reviewed_pilot_policy_construction", path)
    require(spec and spec.loader, "unavailable reviewed generator")
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    inputs = generated["inputs"]
    expected = generator.generate(inputs["hostedZoneId"], inputs["pilotHostname"], inputs["operatorUpdaterPrincipalArn"], inputs["secretsManagerKmsKeyArn"])
    require(generated == expected, "generated policy differs from exact reviewed construction")
    forbidden_secret_overlap([baseline, generated["deployPolicySupplement"]])


def allowed(policies: list[dict], action: str, resource: str, context: dict | None = None) -> bool:
    """Evaluate this authority's IAM subset, including explicit Deny precedence."""
    context = context or {}
    found = False
    for policy in policies:
        require(policy.get("Version") == "2012-10-17", "unsupported IAM policy version")
        for stmt in policy["Statement"]:
            require(set(stmt) <= {"Sid", "Effect", "Action", "Resource", "Condition"}, "unsupported IAM statement")
            require(stmt.get("Effect") in {"Allow", "Deny"}, "invalid IAM effect")
            for op in stmt.get("Condition", {}):
                require(op in {"StringEquals", "ArnEquals", "StringLike", "ForAllValues:StringEquals"}, "unsupported IAM condition")
            require(not any("${" in str(v) for v in (stmt["Action"], stmt["Resource"], stmt.get("Condition", {}))), "IAM policy variables unsupported")
            if not any(iam_match(x.lower(), action.lower()) for x in many(stmt["Action"])):
                continue
            # For an unresolved resource set, ANY applicable deny defeats the
            # all-resources allow claim. Allow statements must cover the set.
            if not any(pattern_relation(x, resource, stmt["Effect"] == "Allow") for x in many(stmt["Resource"])):
                continue
            matched = True
            for op, conditions in stmt.get("Condition", {}).items():
                require(op in {"StringEquals", "ArnEquals", "StringLike", "ForAllValues:StringEquals"}, "unsupported IAM condition")
                for key, expected in conditions.items():
                    values = [] if context.get(key) is None else many(context[key])
                    # IAM ForAllValues is true for a missing/empty request key,
                    # for BOTH Allow and Deny. Ordinary StringEquals is false.
                    matches = [any(iam_match(str(e), str(v)) if op == "StringLike" else v == e for e in many(expected)) for v in values]
                    matched &= all(matches) if op.startswith("ForAllValues:") else bool(values) and any(matches)
            if matched:
                if stmt["Effect"] == "Deny":
                    return False
                found = True
    return found


# Pinned provider request catalog. Each cell is create/read/update/delete;
# data sources have read only. Names are concrete IAM actions, never service '*'.
# This intentionally includes read-after-write, tags, and delete cleanup calls.
LIFECYCLE = {
    "data.aws_availability_zones": ("", "ec2:DescribeAvailabilityZones", "", ""),
    "data.aws_route53_zone": ("", "route53:ListHostedZones route53:GetHostedZone route53:ListTagsForResource", "", ""),
    "data.aws_acm_certificate": ("", "acm:ListCertificates acm:DescribeCertificate acm:ListTagsForCertificate acm:GetCertificate", "", ""),
    "aws_vpc": ("ec2:CreateVpc ec2:CreateTags ec2:ModifyVpcAttribute", "ec2:DescribeVpcs ec2:DescribeVpcAttribute", "ec2:ModifyVpcAttribute ec2:CreateTags ec2:DeleteTags", "ec2:DeleteVpc"),
    "aws_internet_gateway": ("ec2:CreateInternetGateway ec2:AttachInternetGateway ec2:CreateTags", "ec2:DescribeInternetGateways", "ec2:CreateTags ec2:DeleteTags", "ec2:DetachInternetGateway ec2:DeleteInternetGateway"),
    "aws_subnet": ("ec2:CreateSubnet ec2:ModifySubnetAttribute ec2:CreateTags", "ec2:DescribeSubnets", "ec2:ModifySubnetAttribute ec2:CreateTags ec2:DeleteTags", "ec2:DeleteSubnet"),
    "aws_route_table": ("ec2:CreateRouteTable ec2:CreateRoute ec2:CreateTags", "ec2:DescribeRouteTables", "ec2:CreateRoute ec2:ReplaceRoute ec2:DeleteRoute ec2:CreateTags ec2:DeleteTags", "ec2:DeleteRoute ec2:DeleteRouteTable"),
    "aws_route_table_association": ("ec2:AssociateRouteTable", "ec2:DescribeRouteTables", "ec2:ReplaceRouteTableAssociation", "ec2:DisassociateRouteTable"),
    "aws_security_group": ("ec2:CreateSecurityGroup ec2:AuthorizeSecurityGroupIngress ec2:AuthorizeSecurityGroupEgress ec2:RevokeSecurityGroupEgress ec2:CreateTags", "ec2:DescribeSecurityGroups ec2:DescribeSecurityGroupRules ec2:DescribeNetworkInterfaces", "ec2:AuthorizeSecurityGroupIngress ec2:AuthorizeSecurityGroupEgress ec2:RevokeSecurityGroupIngress ec2:RevokeSecurityGroupEgress ec2:CreateTags ec2:DeleteTags", "ec2:RevokeSecurityGroupIngress ec2:RevokeSecurityGroupEgress ec2:DeleteSecurityGroup"),
    "aws_s3_bucket": ("s3:CreateBucket s3:PutBucketTagging", "s3:ListBucket s3:GetBucketLocation s3:GetBucketAcl s3:GetBucketCors s3:GetBucketWebsite s3:GetBucketVersioning s3:GetAccelerateConfiguration s3:GetBucketRequestPayment s3:GetBucketLogging s3:GetLifecycleConfiguration s3:GetReplicationConfiguration s3:GetEncryptionConfiguration s3:GetBucketObjectLockConfiguration s3:GetBucketPolicy s3:GetBucketTagging", "s3:PutBucketTagging", "s3:DeleteBucket"),
    "aws_s3_bucket_public_access_block": ("s3:PutBucketPublicAccessBlock", "s3:GetBucketPublicAccessBlock", "s3:PutBucketPublicAccessBlock", "s3:PutBucketPublicAccessBlock"),
    "aws_s3_bucket_versioning": ("s3:PutBucketVersioning", "s3:GetBucketVersioning", "s3:PutBucketVersioning", "s3:PutBucketVersioning"),
    "aws_s3_bucket_server_side_encryption_configuration": ("s3:PutEncryptionConfiguration", "s3:GetEncryptionConfiguration", "s3:PutEncryptionConfiguration", "s3:PutEncryptionConfiguration"),
    "aws_s3_bucket_lifecycle_configuration": ("s3:PutLifecycleConfiguration", "s3:GetLifecycleConfiguration", "s3:PutLifecycleConfiguration", "s3:PutLifecycleConfiguration"),
    "aws_ecr_repository": ("ecr:CreateRepository ecr:TagResource", "ecr:DescribeRepositories ecr:ListTagsForResource", "ecr:PutImageTagMutability ecr:PutImageScanningConfiguration ecr:TagResource ecr:UntagResource", "ecr:DeleteRepository"),
    "aws_cloudwatch_log_group": ("logs:CreateLogGroup logs:PutRetentionPolicy logs:TagResource", "logs:DescribeLogGroups logs:ListTagsForResource", "logs:PutRetentionPolicy logs:DeleteRetentionPolicy logs:TagResource logs:UntagResource", "logs:DeleteLogGroup"),
    "aws_ecs_cluster": ("ecs:CreateCluster ecs:TagResource", "ecs:DescribeClusters", "ecs:UpdateCluster ecs:UpdateClusterSettings ecs:TagResource ecs:UntagResource", "ecs:DeleteCluster"),
    "aws_ecs_task_definition": ("ecs:RegisterTaskDefinition iam:PassRole", "ecs:DescribeTaskDefinition ecs:ListTagsForResource", "ecs:TagResource ecs:UntagResource", "ecs:DeregisterTaskDefinition"),
    "aws_ecs_service": ("ecs:CreateService", "ecs:DescribeServices", "ecs:UpdateService ecs:TagResource ecs:UntagResource", "ecs:UpdateService ecs:DeleteService"),
    # Budget API operation names differ from their IAM actions. ModifyBudget
    # covers create/update/delete of budgets, notifications and subscribers.
    "aws_budgets_budget": ("budgets:ModifyBudget budgets:TagResource", "budgets:ViewBudget budgets:ListTagsForResource", "budgets:ModifyBudget budgets:TagResource budgets:UntagResource", "budgets:ModifyBudget"),
    "aws_iam_role": ("iam:CreateRole iam:TagRole", "iam:GetRole iam:ListRolePolicies iam:ListAttachedRolePolicies iam:ListInstanceProfilesForRole", "iam:UpdateRole iam:UpdateRoleDescription iam:UpdateAssumeRolePolicy iam:TagRole iam:UntagRole", "iam:DeleteRole"),
    "aws_iam_role_policy": ("iam:PutRolePolicy", "iam:GetRolePolicy", "iam:PutRolePolicy", "iam:DeleteRolePolicy"),
    "aws_iam_role_policy_attachment": ("iam:AttachRolePolicy", "iam:ListAttachedRolePolicies", "iam:AttachRolePolicy iam:DetachRolePolicy", "iam:DetachRolePolicy"),
    "aws_db_subnet_group": ("rds:CreateDBSubnetGroup rds:AddTagsToResource", "rds:DescribeDBSubnetGroups rds:ListTagsForResource", "rds:ModifyDBSubnetGroup rds:AddTagsToResource rds:RemoveTagsFromResource", "rds:DeleteDBSubnetGroup"),
    "aws_db_instance": ("rds:CreateDBInstance rds:AddTagsToResource", "rds:DescribeDBInstances rds:ListTagsForResource", "rds:ModifyDBInstance rds:AddTagsToResource rds:RemoveTagsFromResource", "rds:DeleteDBInstance"),
    "aws_secretsmanager_secret": ("secretsmanager:CreateSecret secretsmanager:TagResource", "secretsmanager:DescribeSecret secretsmanager:GetResourcePolicy", "STOP:secretsmanager:UpdateSecret secretsmanager:TagResource secretsmanager:UntagResource", "secretsmanager:DeleteSecret"),
    "aws_lb": ("elasticloadbalancing:CreateLoadBalancer elasticloadbalancing:AddTags elasticloadbalancing:ModifyLoadBalancerAttributes", "elasticloadbalancing:DescribeLoadBalancers elasticloadbalancing:DescribeLoadBalancerAttributes elasticloadbalancing:DescribeTags", "elasticloadbalancing:ModifyLoadBalancerAttributes elasticloadbalancing:SetSecurityGroups elasticloadbalancing:SetSubnets elasticloadbalancing:SetIpAddressType elasticloadbalancing:AddTags elasticloadbalancing:RemoveTags", "elasticloadbalancing:DeleteLoadBalancer"),
    "aws_lb_target_group": ("elasticloadbalancing:CreateTargetGroup elasticloadbalancing:ModifyTargetGroupAttributes elasticloadbalancing:AddTags", "elasticloadbalancing:DescribeTargetGroups elasticloadbalancing:DescribeTargetGroupAttributes elasticloadbalancing:DescribeTags", "elasticloadbalancing:ModifyTargetGroup elasticloadbalancing:ModifyTargetGroupAttributes elasticloadbalancing:AddTags elasticloadbalancing:RemoveTags", "elasticloadbalancing:DeleteTargetGroup"),
    "aws_lb_listener": ("elasticloadbalancing:CreateListener elasticloadbalancing:AddTags", "elasticloadbalancing:DescribeListeners elasticloadbalancing:DescribeTags", "elasticloadbalancing:ModifyListener elasticloadbalancing:AddTags elasticloadbalancing:RemoveTags", "elasticloadbalancing:DeleteListener"),
    "aws_lb_listener_rule": ("elasticloadbalancing:CreateRule elasticloadbalancing:AddTags", "elasticloadbalancing:DescribeRules elasticloadbalancing:DescribeTags", "elasticloadbalancing:ModifyRule elasticloadbalancing:SetRulePriorities elasticloadbalancing:AddTags elasticloadbalancing:RemoveTags", "elasticloadbalancing:DeleteRule"),
    "aws_route53_record": ("route53:ChangeResourceRecordSets route53:GetChange", "route53:GetHostedZone route53:ListResourceRecordSets", "route53:ChangeResourceRecordSets route53:GetChange", "route53:ChangeResourceRecordSets route53:GetChange"),
    "aws_wafv2_regex_pattern_set": ("wafv2:CreateRegexPatternSet", "wafv2:GetRegexPatternSet wafv2:ListTagsForResource", "wafv2:UpdateRegexPatternSet wafv2:TagResource wafv2:UntagResource", "wafv2:DeleteRegexPatternSet"),
    "aws_wafv2_web_acl": ("wafv2:CreateWebACL", "wafv2:GetWebACL wafv2:ListTagsForResource", "wafv2:UpdateWebACL wafv2:TagResource wafv2:UntagResource", "wafv2:DeleteWebACL"),
    "aws_wafv2_web_acl_association": ("wafv2:AssociateWebACL", "wafv2:GetWebACLForResource", "wafv2:AssociateWebACL wafv2:DisassociateWebACL", "wafv2:DisassociateWebACL"),
    "aws_scheduler_schedule": ("scheduler:CreateSchedule iam:PassRole", "scheduler:GetSchedule scheduler:ListSchedules", "scheduler:UpdateSchedule iam:PassRole", "scheduler:DeleteSchedule"),
}


def bound_sources(root: Path = ROOT) -> dict[str, str]:
    matrix = json.loads((root / "infra/aws-iam/pilot-policy-matrix.json").read_text())
    directory = root / "infra/terraform"
    require(not list(directory.glob("*.tf.json")), "JSON Terraform configuration is not reviewed")
    require(not any(p.name == "override.tf" or p.name.endswith("_override.tf") for p in directory.glob("*.tf")), "Terraform override configuration is not reviewed")
    files = {p.name: p.read_text() for p in directory.glob("*.tf")}
    require({name: hashlib.sha256(source.encode()).hexdigest() for name, source in files.items()} == matrix["executableAuthority"]["terraformSourceSha256"], "Terraform source drift: refresh catalog and independent review")
    require('version = "= 5.100.0"' in files["versions.tf"], "provider version drift")
    return files


def instances(sources: dict[str, str]) -> dict[str, str]:
    result = {}
    for source in sources.values():
        for kind, typ, name in re.findall(r'^(resource|data) "([^"]+)" "([^"]+)"', source, re.M):
            address = ("data." if kind == "data" else "") + typ + "." + name
            if typ == "terraform_data" or typ == "aws_iam_policy_document":
                result[address] = "local"
                continue
            require(typ.startswith("aws_"), "unreviewed provider")
            keys = [""]
            if address in {"aws_iam_role.ecs_execution", "aws_iam_role_policy_attachment.ecs_execution_managed"}:
                keys = [f'["{x}"]' for x in ("api", "frontend", "worker", "bootstrap")]
            elif address == "aws_ecs_task_definition.bootstrap":
                keys = [f'["{x}"]' for x in ("migration", "reference", "runtime-role", "first-admin")]
            elif address in {"aws_subnet.public", "aws_subnet.private", "aws_route_table_association.public"}:
                keys = ["[0]", "[1]"]
            for key in keys:
                result[address + key] = ("data." if kind == "data" else "") + typ
    return result


def role_resource(address: str) -> str:
    name = address.split(".", 1)[1]
    if "[" in name:
        name = json.loads(name[name.index("[") + 1:-1]) + "_execution"
    names = {"api_execution_secrets": "api-execution", "worker_execution_secrets": "worker-execution",
             "migration_reference_secrets": "migration-reference-task", "runtime_role_secrets": "runtime-role-task",
             "first_admin_secrets": "first-admin-task"}
    name = names.get(name, name.replace("_", "-"))
    return f"arn:aws:iam::{ACCOUNT}:role/paprnav-pilot-{name}-role"


def requirements(sources: dict[str, str], inputs: dict) -> list[dict]:
    """Expand the pinned current graph, including explicit for_each/count members."""
    rows = []
    region_context = {"aws:RequestedRegion": REGION, "aws:RequestTag/Project": "paprnav"}
    for address, typ in instances(sources).items():
        if typ == "local":
            rows.append({"address": address, "phase": "local", "decision": "local-only"})
            continue
        require(typ in LIFECYCLE, f"uncatalogued Terraform type: {typ}")
        for phase, actions in zip(("create", "read", "update", "delete"), LIFECYCLE[typ]):
            for action in actions.split():
                context = dict(region_context)
                scope = "*"
                stop = action.startswith("STOP:")
                action = action.removeprefix("STOP:")
                if typ.startswith("aws_s3_"):
                    bucket = "artifacts" if address.endswith("app_artifacts") else "terraform-state"
                    scope = f"arn:aws:s3:::paprnav-pilot-{bucket}-{ACCOUNT}"
                elif typ.startswith("aws_ecr_"):
                    scope = f"arn:aws:ecr:{REGION}:{ACCOUNT}:repository/paprnav/pilot-{address.split('.')[-1]}"
                elif typ == "aws_cloudwatch_log_group" and not action.startswith("logs:Describe"):
                    scope = f"arn:aws:logs:{REGION}:{ACCOUNT}:log-group:/paprnav/pilot/{address.split('.')[-1]}:*"
                elif typ == "aws_db_instance" and not action.startswith("rds:Describe"):
                    scope = f"arn:aws:rds:{REGION}:{ACCOUNT}:db:paprnav-pilot"
                elif typ == "aws_db_subnet_group" and not action.startswith("rds:Describe"):
                    scope = f"arn:aws:rds:{REGION}:{ACCOUNT}:subgrp:paprnav-pilot"
                elif typ == "aws_budgets_budget":
                    scope = f"arn:aws:budgets::{ACCOUNT}:budget/paprnav-pilot-monthly"
                elif typ.startswith("aws_iam_"):
                    scope = role_resource(address)
                elif typ == "aws_secretsmanager_secret":
                    scope = f"arn:aws:secretsmanager:{REGION}:{ACCOUNT}:secret:{SECRET_NAMES[address]}-*"
                elif action.startswith("route53:") and action not in {"route53:ListHostedZones", "route53:GetChange"}:
                    scope = "arn:aws:route53:::hostedzone/" + inputs["hostedZoneId"]
                    if action == "route53:ChangeResourceRecordSets":
                        context.update({"route53:ChangeResourceRecordSetsNormalizedRecordNames": [inputs["pilotHostname"]], "route53:ChangeResourceRecordSetsRecordTypes": ["A"], "route53:ChangeResourceRecordSetsActions": [{"create": "CREATE", "update": "UPSERT", "delete": "DELETE"}[phase]]})
                elif action.startswith("acm:") and action != "acm:ListCertificates":
                    scope = f"arn:aws:acm:{REGION}:{ACCOUNT}:certificate/*"
                elif action.startswith("scheduler:") and action != "scheduler:ListSchedules":
                    scope = f"arn:aws:scheduler:{REGION}:{ACCOUNT}:schedule/default/paprnav-pilot-worker"
                elif action.startswith("wafv2:") and action not in {"wafv2:CreateWebACL", "wafv2:CreateRegexPatternSet", "wafv2:GetWebACLForResource"}:
                    name = address.split(".")[-1].replace("_", "-")
                    kind = "regexpatternset" if typ == "aws_wafv2_regex_pattern_set" else "webacl"
                    name = name if kind == "regexpatternset" else "web-acl"
                    scope = f"arn:aws:wafv2:{REGION}:{ACCOUNT}:regional/{kind}/paprnav-pilot-{name}/*"
                if action == "iam:PassRole":
                    if typ == "aws_scheduler_schedule":
                        roles = [role_resource("aws_iam_role.worker_scheduler")]
                        context["iam:PassedToService"] = "scheduler.amazonaws.com"
                    else:
                        name = address.split(".", 1)[1]
                        key = "bootstrap" if name.startswith("bootstrap[") else name
                        task = {"migration": "migration_reference", "reference": "migration_reference", "runtime-role": "runtime_role", "first-admin": "first_admin"}.get(json.loads(name[name.index("[") + 1:-1]) if "[" in name else name, name)
                        roles = [role_resource(f'aws_iam_role.ecs_execution["{key}"]'), role_resource(f"aws_iam_role.{task}_task")]
                        context["iam:PassedToService"] = "ecs-tasks.amazonaws.com"
                else:
                    roles = [scope]
                if action in {"wafv2:AssociateWebACL", "wafv2:DisassociateWebACL"}:
                    roles.append(f"arn:aws:elasticloadbalancing:{REGION}:{ACCOUNT}:loadbalancer/app/paprnav-pilot/*")
                for resource in roles:
                    rows.append({"address": address, "phase": phase, "action": action, "resource": resource, "context": context, "decision": "stop-secret-update" if stop else "allow"})
        # Dependency permissions are part of each concrete consumer's lifecycle.
        service = {"aws_db_instance": ("rds.amazonaws.com", "RDS"), "aws_ecs_cluster": ("ecs.amazonaws.com", "ECS"), "aws_lb": ("elasticloadbalancing.amazonaws.com", "ElasticLoadBalancing")}.get(typ)
        if service:
            rows.append({"address": address, "phase": "create", "action": "iam:CreateServiceLinkedRole", "resource": f"arn:aws:iam::{ACCOUNT}:role/aws-service-role/{service[0]}/AWSServiceRoleFor{service[1]}", "context": {"iam:AWSServiceName": service[0]}, "decision": "allow"})
        if typ == "aws_db_instance":
            for action, resource, context in [
                ("secretsmanager:CreateSecret", "*", {"aws:RequestedRegion": REGION, "secretsmanager:Name": "rds!db-*"}),
                ("secretsmanager:TagResource", f"arn:aws:secretsmanager:{REGION}:{ACCOUNT}:secret:rds!db-*", {}),
                ("kms:DescribeKey", inputs["secretsManagerKmsKeyArn"], {}),
            ]:
                rows.append({"address": address, "phase": "create", "action": action, "resource": resource, "context": context, "decision": "allow"})
    return rows


def coverage(generated: dict, baseline: dict, root: Path = ROOT) -> dict:
    policy_contract(generated, baseline, root)
    sources = bound_sources(root)
    policies = [baseline, generated["deployPolicySupplement"]]
    rows = requirements(sources, generated["inputs"])
    for row in rows:
        if row["decision"] == "local-only":
            continue
        matches = [name for name, policy in zip(("baseline", "supplement"), policies) if allowed([policy], row["action"], row["resource"], row["context"])]
        if row["decision"] == "stop-secret-update":
            require(not allowed(policies, row["action"], row["resource"], row["context"]), "UpdateSecret unexpectedly allowed")
            row["authority"] = "plan_gate"
        else:
            require(allowed(policies, row["action"], row["resource"], row["context"]), f"uncovered lifecycle: {row}")
            row["authority"] = matches
    runtime_boundary(sources)
    return {"status": "pass", "provider": "hashicorp/aws@5.100.0", "instances": len(instances(sources)), "requirements": rows, "policySha256": digest(policies)}


def blocks(source: str, opener: str) -> list[str]:
    """Read balanced HCL blocks while respecting quoted strings (closed source)."""
    result = []
    for match in re.finditer(opener + r"\s*\{", source):
        start = match.end()
        depth, quoted, escaped = 1, False, False
        for index in range(start, len(source)):
            char = source[index]
            if quoted:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    quoted = False
            elif char == '"':
                quoted = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    result.append(source[start:index])
                    break
        else:
            raise Stop("unbalanced source")
    return result


def runtime_boundary(sources: dict[str, str]) -> None:
    """Check the actual policy-document actions/resources and actual attachments.

    Exact source identities also bind conditions, managed attachments, task-role
    references and trust relationships; changes require recataloguing/review.
    """
    source = sources["ecs_runtime.tf"]
    reads = {"secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"}
    artifact = {"s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:GetObjectTagging", "s3:PutObjectTagging"}
    db = "aws_secretsmanager_secret.database_url.arn"
    admin = "aws_db_instance.postgres.master_user_secret[0].secret_arn"
    bucket = "aws_s3_bucket.app_artifacts.arn"
    expected = {
        "api_execution_secrets": [(reads, {db, "aws_secretsmanager_secret.invitation_signing.arn"})],
        "worker_execution_secrets": [(reads, {db})],
        "api_task": [(artifact, {'"${' + bucket + '}/*"'}), ({"s3:ListBucket"}, {bucket})],
        "worker_task": [(artifact, {'"${' + bucket + '}/*"'}), ({"s3:ListBucket"}, {bucket}), ({"textract:DetectDocumentText", "textract:StartDocumentTextDetection", "textract:GetDocumentTextDetection"}, {'"*"'})],
        "migration_reference_secrets": [(reads, {admin})],
        "runtime_role_secrets": [(reads, {admin}), ({"secretsmanager:PutSecretValue", "secretsmanager:DescribeSecret"}, {db})],
        "first_admin_secrets": [(reads, {admin, "aws_secretsmanager_secret.first_admin_password.arn"})],
        "worker_scheduler": [({"ecs:RunTask"}, {"aws_ecs_task_definition.worker.arn"}), ({"iam:PassRole"}, {'aws_iam_role.ecs_execution["worker"].arn', "aws_iam_role.worker_task.arn"})],
    }
    for name, expected_statements in expected.items():
        documents = blocks(source, rf'data "aws_iam_policy_document" "{name}"')
        require(len(documents) == 1, f"missing runtime document {name}")
        actual = []
        for stmt in blocks(documents[0], r"statement"):
            actions = re.search(r"actions\s*=\s*(\[[^\n]+\])", stmt)
            resources = re.search(r"resources\s*=\s*\[(.*?)\]\s*(?:\n|$)", stmt, re.S)
            require(actions and resources, "unsupported runtime policy expression")
            actual.append((set(json.loads(actions[1])), {x.strip() for x in resources[1].split(",") if x.strip()}))
        require(actual == expected_statements, f"runtime authority drift: {name}")
    require('role   = aws_iam_role.frontend_task' not in source, "frontend policy attachment")


def has_unknown(value: Any) -> bool:
    if isinstance(value, dict):
        return any(has_unknown(v) for v in value.values())
    if isinstance(value, list):
        return any(has_unknown(v) for v in value)
    return value is True


def validate_plan_changes(plan: dict, generated: dict, baseline: dict, root: Path = ROOT) -> dict:
    """Pure change checks, not an approval result; saved-plan binding is required."""
    proof = coverage(generated, baseline, root)
    require(plan.get("format_version") == "1.2", "unsupported/missing Terraform plan format")
    require(plan.get("errored") is False and plan.get("complete") is True, "incomplete/errored/targeted plan")
    require(not plan.get("deferred_changes"), "deferred changes")
    variables = plan.get("variables", {})
    for key, value in {"project": "paprnav", "environment": "pilot", "aws_account_id": ACCOUNT, "aws_region": REGION}.items():
        require(variables.get(key, {}).get("value") == value, f"unknown or drifted input: {key}")
    require(variables.get("route53_zone_id", {}).get("value") == generated["inputs"]["hostedZoneId"], "zone input differs from policy")
    require(variables.get("pilot_hostname", {}).get("value") == generated["inputs"]["pilotHostname"], "hostname input differs from policy")
    known = instances(bound_sources(root))
    changes = plan.get("resource_changes")
    require(isinstance(changes, list), "missing resource changes")
    seen = set()
    for item in changes:
        address = item["address"]
        require(address in known and address not in seen, f"unknown/duplicate resource instance: {address}")
        if known[address] != "local":
            require(item.get("type") == known[address].removeprefix("data."), "resource type/address mismatch")
        seen.add(address)
        if item.get("type") == "aws_secretsmanager_secret" or address in SECRET_NAMES:
            require(address in SECRET_NAMES and item.get("type") == "aws_secretsmanager_secret", "uncatalogued secret")
            change = item["change"]
            require(change["actions"] in [["create"], ["update"], ["no-op"]], "secret destroy/replacement is outside foundation gate")
            before, after = change.get("before"), change.get("after")
            require(isinstance(after, dict), "unknown secret after state")
            unknown = change.get("after_unknown")
            require(isinstance(unknown, dict), "missing secret unknown metadata")
            # Computed IDs on creates are the only accepted unknowns. Unknown
            # description/name/KMS/tags or any unrecognized field stops all apply.
            computed = {"arn", "id", "policy", "name_prefix", "replica"} if change["actions"] == ["create"] else set()
            require(not has_unknown({k: v for k, v in unknown.items() if k not in computed}), "unknown secret inputs")
            for value in [after] + ([before] if before is not None else []):
                require(isinstance(value, dict) and value.get("name") == SECRET_NAMES[address], "legacy or unknown secret name")
                require("description" in value and "kms_key_id" in value, "incomplete secret metadata")
                require(isinstance(value["description"], str), "unknown secret description")
                require(value["kms_key_id"] is None or isinstance(value["kms_key_id"], str), "unknown secret KMS input")
                if value.get("arn"):
                    require(re.fullmatch(rf"arn:aws:secretsmanager:{REGION}:{ACCOUNT}:secret:{re.escape(SECRET_NAMES[address])}-[A-Za-z0-9]{{6}}", value["arn"]), "secret ARN/name drift")
            if change["actions"] == ["create"]:
                require(before is None, "create has previous secret")
                require(after["kms_key_id"] in {None, ""}, "custom secret KMS creation requires separate authority review")
                require(not after.get("replica") and not after.get("policy") and not after.get("name_prefix"), "unreviewed secret create inputs")
            else:
                require(isinstance(before, dict), "missing secret before state")
                for key in set(before) | set(after):
                    if key not in {"tags", "tags_all"}:
                        require(before.get(key) == after.get(key), f"secret update requires stop: {address}.{key}")
    require(set(SECRET_NAMES) <= seen, "plan does not include all three secret resources")
    require({a for a, typ in known.items() if typ != "local" and not typ.startswith("data.")} <= seen, "plan omits managed graph instances")
    return {"status": "checks-pass", "decision": "saved-plan-binding-required", "planSha256": digest(plan), "policySha256": proof["policySha256"], "mutationAuthorized": False}


def saved_configuration(saved: bytes, sources: dict[str, str]) -> str:
    """Bind every embedded module/file from the actual Terraform plan archive."""
    try:
        with zipfile.ZipFile(io.BytesIO(saved)) as archive:
            names = archive.namelist()
            require(len(names) == len(set(names)), "duplicate plan archive members")
            require("tfplan" in names, "missing binary Terraform plan")
            modules = json.loads(archive.read("tfconfig/modules.json"))
            require(modules == [{"Key": "", "Dir": "."}], "unreviewed Terraform module graph")
            expected = {"tfconfig/m-/" + name: source.encode() for name, source in sources.items()}
            actual = {name: archive.read(name) for name in names if name.startswith("tfconfig/") and name != "tfconfig/modules.json"}
            require(actual == expected, "saved plan configuration differs from reviewed configuration")
    except (zipfile.BadZipFile, KeyError, UnicodeError) as exc:
        raise Stop("invalid saved Terraform configuration") from exc
    return digest({name: hashlib.sha256(data).hexdigest() for name, data in expected.items()})


def plan_gate(plan: dict, generated: dict, baseline: dict, root: Path = ROOT, *, saved_plan: Path | None = None, terraform_bin: str = "terraform") -> dict:
    """Only pass when the exact binary's sources AND JSON match the evidence.

    terraform show is read-only and decodes the saved plan, without refreshing,
    planning, backend locking or applying. The trusted operator-installed binary
    is an external evidence reader, like the AWS CLI used to capture IAM pages.
    """
    require(saved_plan is not None, "--saved-plan is required for configuration binding")
    saved = saved_plan.read_bytes()
    config_hash = saved_configuration(saved, bound_sources(root))
    shown = subprocess.run([terraform_bin, "show", "-json", str(saved_plan.resolve())], cwd=root / "infra/terraform", capture_output=True, text=True, check=False, timeout=60)
    require(shown.returncode == 0, "Terraform could not render the exact saved plan")
    require(json.loads(shown.stdout) == plan, "plan JSON differs from exact saved binary rendering")
    require(saved_plan.read_bytes() == saved, "saved plan changed during verification")
    result = validate_plan_changes(plan, generated, baseline, root)
    result.update(status="pass", decision="eligible-for-M6-review", savedPlanSha256=hashlib.sha256(saved).hexdigest(), configurationSha256=config_hash)
    return result


def pages(records: list, operation: str, fixed_request: dict, result_keys: tuple[str, ...]) -> dict[str, list]:
    """Validate raw request/response page chain, not a caller's 'complete' flag."""
    require(isinstance(records, list) and records, f"missing {operation} pages")
    result = {key: [] for key in result_keys}
    marker = None
    used = set()
    for index, record in enumerate(records):
        request = dict(fixed_request)
        if marker is not None:
            request["Marker"] = marker
        require(record.get("request") == request, f"wrong {operation} request/page marker")
        response = record.get("response", {})
        require(type(response.get("IsTruncated")) is bool, f"unknown {operation} truncation")
        for key in result_keys:
            require(isinstance(response.get(key), list), f"missing {operation} {key}")
            result[key].extend(response[key])
        if response["IsTruncated"]:
            marker = response.get("Marker")
            require(isinstance(marker, str) and marker and marker not in used, f"invalid {operation} continuation")
            used.add(marker)
            require(index < len(records) - 1, f"incomplete {operation} pagination")
        else:
            require(index == len(records) - 1 and not response.get("Marker"), f"unexpected {operation} trailing pages/marker")
    return result


def snapshot(state: dict) -> dict:
    """Validate observed IAM evidence without accepting inference from denials."""
    require(state.get("policyArn") == POLICY and state.get("roleArn") == ROLE, "wrong publication targets")
    require("policy" in state, "missing GetPolicy outcome")
    if state["policy"] is not None:
        require(state.get("getPolicyError") is None, "contradictory GetPolicy success/error evidence")
    attachments = pages(state.get("rolePolicyPages"), "ListAttachedRolePolicies", {"RoleName": ROLE.rsplit("/", 1)[1]}, ("AttachedPolicies",))["AttachedPolicies"]
    attached_arns = [p["PolicyArn"] for p in attachments]
    require(len(attached_arns) == len(set(attached_arns)), "duplicate role attachment")
    require(POLICY.removesuffix("-pilot-supplement") in attached_arns, "baseline attachment absent")
    quotas = state.get("quotas", {})
    for key in ("rolePolicyLimit", "policyCount", "policyLimit"):
        require(type(quotas.get(key)) is int and quotas[key] >= 0, "unknown IAM quota")
    require(len(attachments) <= quotas["rolePolicyLimit"] and quotas["policyCount"] <= quotas["policyLimit"], "inconsistent quota inventory")
    policy = state.get("policy")
    attached = POLICY in attached_arns
    if policy is None:
        require(state.get("getPolicyError") == "NoSuchEntity", "absence not proved by GetPolicy")
        require(not attached and state.get("entityPages") == {} and state.get("versionPages") == [], "inconsistent absent policy inventory")
        return {"exists": False, "attached": False, "versions": {}, "default": None, "policyId": None, "attachments": attached_arns, "quotas": quotas}
    require(policy.get("Arn") == POLICY and isinstance(policy.get("PolicyId"), str) and policy["PolicyId"], "unbound policy identity")
    uses = {}
    for usage in ("PermissionsPolicy", "PermissionsBoundary"):
        uses[usage] = pages(state.get("entityPages", {}).get(usage), "ListEntitiesForPolicy", {"PolicyArn": POLICY, "PolicyUsageFilter": usage}, ("PolicyRoles", "PolicyUsers", "PolicyGroups"))
    require(all(not entries for entries in uses["PermissionsBoundary"].values()), "permissions-boundary consumer")
    consumers = uses["PermissionsPolicy"]
    require(not consumers["PolicyUsers"] and not consumers["PolicyGroups"], "shared user/group consumer")
    roles = consumers["PolicyRoles"]
    require(all(r.get("RoleName") == ROLE.rsplit("/", 1)[1] for r in roles) and len(roles) <= 1, "shared/later-page role consumer")
    require(bool(roles) == attached and policy.get("AttachmentCount") == len(roles) and policy.get("PermissionsBoundaryUsageCount") == 0, "consumer/attachment inventory disagreement")
    versions = pages(state.get("versionPages"), "ListPolicyVersions", {"PolicyArn": POLICY}, ("Versions",))["Versions"]
    require(0 < len(versions) <= 5, "invalid version count")
    ids = [v.get("VersionId") for v in versions]
    require(all(isinstance(v, str) and re.fullmatch(r"v[1-9][0-9]*", v) for v in ids) and len(set(ids)) == len(ids), "invalid/duplicate version IDs")
    require(all(type(v.get("IsDefaultVersion")) is bool and re.fullmatch(r"[a-f0-9]{64}", v.get("DocumentSha256", "")) for v in versions), "missing version document proof")
    defaults = [v["VersionId"] for v in versions if v["IsDefaultVersion"]]
    require(defaults == [policy.get("DefaultVersionId")], "default version disagreement")
    return {"exists": True, "attached": attached, "versions": {v["VersionId"]: v["DocumentSha256"] for v in versions}, "default": defaults[0], "policyId": policy["PolicyId"], "attachments": attached_arns, "quotas": quotas}


def step(action: str, **parameters: Any) -> dict:
    return {"action": action, "parameters": parameters}


def publication(pre: dict, candidate_sha256: str, observed: dict | None = None) -> dict:
    require(re.fullmatch(r"[a-f0-9]{64}", candidate_sha256), "invalid candidate hash")
    before = snapshot(pre)
    steps = []
    if observed is None:
        require(before["attached"] or len(before["attachments"]) < before["quotas"]["rolePolicyLimit"], "attachment quota exhausted")
        if before["exists"]:
            require(len(before["versions"]) < 5, "version quota exhausted; deletion not authorized")
            steps.append(step("iam:CreatePolicyVersion", PolicyArn=POLICY, SetAsDefault=True, DocumentSha256=candidate_sha256))
        else:
            require(before["quotas"]["policyCount"] < before["quotas"]["policyLimit"], "managed policy quota exhausted")
            steps.append(step("iam:CreatePolicy", PolicyName=POLICY.rsplit("/", 1)[1], DocumentSha256=candidate_sha256, Tags=[{"Key": "Project", "Value": "paprnav"}]))
        if not before["attached"]:
            steps.append(step("iam:AttachRolePolicy", RoleName=ROLE.rsplit("/", 1)[1], PolicyArn=POLICY))
        branch = "attached-existing" if before["attached"] else "detached-existing" if before["exists"] else "absent"
        return {"status": "pass", "branch": branch, "steps": steps, "preStateSha256": digest(pre), "candidateSha256": candidate_sha256, "mutationAuthorized": False, "protocol": "Execute only after M1 authorization. Re-read and revalidate after EACH call; ambiguous outcome goes to recovery, never blind retry."}
    after = snapshot(observed)
    require(set(before["attachments"]) - {POLICY} == set(after["attachments"]) - {POLICY}, "unrelated role attachments changed")
    if before["exists"]:
        require(after["exists"] and before["policyId"] == after["policyId"], "policy deleted/recreated; manual recovery required")
        require(all(after["versions"].get(v) == h for v, h in before["versions"].items()), "prior version missing/changed")
    new_versions = set(after["versions"]) - set(before["versions"])
    require(len(new_versions) <= 1 and all(after["versions"][v] == candidate_sha256 for v in new_versions), "unattributed version change")
    if before["exists"] and after["default"] != before["default"]:
        steps.append(step("iam:SetDefaultPolicyVersion", PolicyArn=POLICY, VersionId=before["default"]))
    if before["attached"] != after["attached"]:
        if before["attached"]:
            require(len(after["attachments"]) < after["quotas"]["rolePolicyLimit"], "recovery attachment quota exhausted")
        steps.append(step("iam:AttachRolePolicy" if before["attached"] else "iam:DetachRolePolicy", RoleName=ROLE.rsplit("/", 1)[1], PolicyArn=POLICY))
    residual = sorted(new_versions)
    return {"status": "pass", "decision": "recovery-review", "steps": steps, "targetDefault": before["default"], "targetAttached": before["attached"], "residualVersions": residual, "residualNewPolicy": not before["exists"] and after["exists"], "deletionAuthorized": False, "mutationAuthorized": False, "preStateSha256": digest(pre), "observedStateSha256": digest(observed), "protocol": "Re-read after each recovery call; re-run until steps is empty. Residual policy/versions require separate deletion approval."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("coverage", "plan", "publication", "recovery"))
    parser.add_argument("--generated", type=Path)
    parser.add_argument("--plan-json", type=Path)
    parser.add_argument("--saved-plan", type=Path)
    parser.add_argument("--terraform-bin", default="terraform", help="trusted local Terraform executable for read-only show")
    parser.add_argument("--pre-state", type=Path)
    parser.add_argument("--observed-state", type=Path)
    parser.add_argument("--candidate-sha256")
    args = parser.parse_args()
    try:
        read = lambda p: json.loads(p.read_text())
        if args.command in {"coverage", "plan"}:
            require(args.generated is not None, "--generated is required")
            generated = read(args.generated)
            baseline = read(ROOT / "infra/aws-iam/paprnav-terraform-deploy-policy.json")
            if args.command == "coverage":
                result = coverage(generated, baseline)
            else:
                require(args.plan_json is not None, "--plan-json is required")
                result = plan_gate(read(args.plan_json), generated, baseline, saved_plan=args.saved_plan, terraform_bin=args.terraform_bin)
                result["planFileSha256"] = hashlib.sha256(args.plan_json.read_bytes()).hexdigest()
        else:
            require(args.pre_state is not None and args.candidate_sha256 is not None, "pre-state and candidate hash required")
            require(args.command != "recovery" or args.observed_state is not None, "recovery requires newly observed state")
            result = publication(read(args.pre_state), args.candidate_sha256, read(args.observed_state) if args.command == "recovery" else None)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (Stop, KeyError, TypeError, ValueError, OSError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"status": "stop", "reason": str(exc), "mutationAuthorized": False}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
