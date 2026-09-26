#!/usr/bin/env python3
"""Generate bounded pilot prerequisite IAM documents from explicit inputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any


ACCOUNT = "527257972989"
REGION = "us-east-1"
DEPLOY_POLICY_ARN = f"arn:aws:iam::{ACCOUNT}:policy/paprnav-terraform-deploy"
SUPPLEMENT_POLICY_ARN = f"{DEPLOY_POLICY_ARN}-pilot-supplement"
DEPLOY_ROLE_ARN = f"arn:aws:iam::{ACCOUNT}:role/paprnav-terraform-deploy"
WORKER_SCHEDULE_ARN = f"arn:aws:scheduler:{REGION}:{ACCOUNT}:schedule/default/paprnav-pilot-worker"
WORKER_SCHEDULER_ROLE_ARN = f"arn:aws:iam::{ACCOUNT}:role/paprnav-pilot-worker-scheduler-role"
PRINCIPAL_RE = re.compile(rf"^arn:aws:iam::{ACCOUNT}:(?:user|role)/[^\s]+$")
KMS_RE = re.compile(rf"^arn:aws:kms:{REGION}:{ACCOUNT}:key/[0-9a-f-]+$")
HOSTNAME_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)+$")
PILOT_HOSTNAME = "pilot.paprnav.com"
DNS_ZONE_NAME = "paprnav.com"
DNS_PROVIDER = "Squarespace"


def statement(sid: str, actions: list[str], resource: str | list[str], condition: dict[str, Any] | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"Sid": sid, "Effect": "Allow", "Action": actions, "Resource": resource}
    if condition:
        result["Condition"] = condition
    return result


def generate(dns_zone_name: str, pilot_hostname: str, updater_principal: str, kms_key_arn: str) -> dict[str, Any]:
    if dns_zone_name != DNS_ZONE_NAME or HOSTNAME_RE.fullmatch(dns_zone_name) is None:
        raise ValueError(f"DNS zone must be the Squarespace-managed {DNS_ZONE_NAME}")
    if pilot_hostname != PILOT_HOSTNAME or HOSTNAME_RE.fullmatch(pilot_hostname) is None:
        raise ValueError(f"pilot hostname must be {PILOT_HOSTNAME}")
    if pilot_hostname == dns_zone_name or not pilot_hostname.endswith(f".{dns_zone_name}"):
        raise ValueError("pilot hostname must be a subdomain of the Squarespace DNS zone")
    if PRINCIPAL_RE.fullmatch(updater_principal) is None:
        raise ValueError("updater principal must be an exact account IAM user or role ARN")
    if KMS_RE.fullmatch(kms_key_arn) is None:
        raise ValueError("Secrets Manager KMS key must be one exact account/region key ARN")
    deploy_statements = [
        statement(
            "AcmInventory",
            ["acm:ListCertificates"],
            "*",
            {"StringEquals": {"aws:RequestedRegion": REGION}},
        ),
        statement(
            "AcmCertificateMetadata",
            ["acm:DescribeCertificate", "acm:ListTagsForCertificate", "acm:GetCertificate"],
            f"arn:aws:acm:{REGION}:{ACCOUNT}:certificate/*",
            {"StringEquals": {"aws:RequestedRegion": REGION}},
        ),
        statement(
            "WafInventory",
            ["wafv2:ListWebACLs", "wafv2:ListRegexPatternSets", "wafv2:GetWebACLForResource"],
            "*",
            {"StringEquals": {"aws:RequestedRegion": REGION}},
        ),
        statement(
            "WafCreateTaggedPilotResources",
            ["wafv2:CreateWebACL", "wafv2:CreateRegexPatternSet"],
            "*",
            {"StringEquals": {
                "aws:RequestedRegion": REGION,
                "aws:RequestTag/Project": "paprnav",
                "aws:RequestTag/Environment": "pilot",
            }},
        ),
        statement(
            "WafManagePilotResources",
            ["wafv2:GetWebACL", "wafv2:UpdateWebACL", "wafv2:DeleteWebACL", "wafv2:GetRegexPatternSet", "wafv2:UpdateRegexPatternSet", "wafv2:DeleteRegexPatternSet", "wafv2:ListTagsForResource", "wafv2:TagResource", "wafv2:UntagResource"],
            [
                f"arn:aws:wafv2:{REGION}:{ACCOUNT}:regional/webacl/paprnav-*/*",
                f"arn:aws:wafv2:{REGION}:{ACCOUNT}:regional/regexpatternset/paprnav-*/*",
            ],
        ),
        statement(
            "WafAssociatePilotAlb",
            ["wafv2:AssociateWebACL", "wafv2:DisassociateWebACL"],
            [f"arn:aws:wafv2:{REGION}:{ACCOUNT}:regional/webacl/paprnav-*/*", f"arn:aws:elasticloadbalancing:{REGION}:{ACCOUNT}:loadbalancer/app/paprnav-pilot/*"],
        ),
        statement(
            "SchedulerInventory",
            ["scheduler:ListSchedules"],
            "*",
            {"StringEquals": {"aws:RequestedRegion": REGION}},
        ),
        statement(
            "ManageExactWorkerSchedule",
            ["scheduler:GetSchedule", "scheduler:CreateSchedule", "scheduler:UpdateSchedule", "scheduler:DeleteSchedule"],
            WORKER_SCHEDULE_ARN,
            {"StringEquals": {"aws:RequestedRegion": REGION}},
        ),
        statement(
            "PassExactWorkerSchedulerRole",
            ["iam:PassRole"],
            WORKER_SCHEDULER_ROLE_ARN,
            {"StringEquals": {"iam:PassedToService": "scheduler.amazonaws.com"}},
        ),
        statement(
            "CreateTaggedPilotSecrets",
            ["secretsmanager:CreateSecret"],
            "*",
            {
                "StringLike": {"secretsmanager:Name": "/paprnav/pilot/*"},
                "StringEquals": {
                    "aws:RequestedRegion": REGION,
                    "aws:RequestTag/Project": "paprnav",
                    "aws:RequestTag/Environment": "pilot",
                },
            },
        ),
        statement(
            "ManagePilotSecretLifecycleWithoutValues",
            ["secretsmanager:TagResource", "secretsmanager:UntagResource", "secretsmanager:DeleteSecret", "secretsmanager:RestoreSecret"],
            f"arn:aws:secretsmanager:{REGION}:{ACCOUNT}:secret:/paprnav/pilot/*",
        ),
        statement(
            "CreateRdsManagedSecret",
            ["secretsmanager:CreateSecret"],
            "*",
            {"StringLike": {"secretsmanager:Name": "rds!db-*"}, "StringEquals": {"aws:RequestedRegion": REGION}},
        ),
        statement(
            "TagRdsManagedSecret",
            ["secretsmanager:TagResource"],
            f"arn:aws:secretsmanager:{REGION}:{ACCOUNT}:secret:rds!db-*",
        ),
        statement(
            "CreateRdsServiceLinkedRole",
            ["iam:CreateServiceLinkedRole"],
            f"arn:aws:iam::{ACCOUNT}:role/aws-service-role/rds.amazonaws.com/AWSServiceRoleForRDS",
            {"StringEquals": {"iam:AWSServiceName": "rds.amazonaws.com"}},
        ),
        statement(
            "CreateEcsServiceLinkedRole",
            ["iam:CreateServiceLinkedRole"],
            f"arn:aws:iam::{ACCOUNT}:role/aws-service-role/ecs.amazonaws.com/AWSServiceRoleForECS",
            {"StringEquals": {"iam:AWSServiceName": "ecs.amazonaws.com"}},
        ),
        statement(
            "CreateElbServiceLinkedRole",
            ["iam:CreateServiceLinkedRole"],
            f"arn:aws:iam::{ACCOUNT}:role/aws-service-role/elasticloadbalancing.amazonaws.com/AWSServiceRoleForElasticLoadBalancing",
            {"StringEquals": {"iam:AWSServiceName": "elasticloadbalancing.amazonaws.com"}},
        ),
    ]
    operator = {
        "Version": "2012-10-17",
        "Statement": [
            statement(
                "ManageExactPilotSupplement",
                [
                    "iam:CreatePolicy",
                    "iam:GetPolicy",
                    "iam:GetPolicyVersion",
                    "iam:ListPolicyVersions",
                    "iam:ListEntitiesForPolicy",
                    "iam:CreatePolicyVersion",
                    "iam:SetDefaultPolicyVersion",
                    "iam:TagPolicy",
                ],
                SUPPLEMENT_POLICY_ARN,
            ),
            statement(
                "AttachExactPilotSupplement",
                ["iam:AttachRolePolicy", "iam:DetachRolePolicy"],
                DEPLOY_ROLE_ARN,
                {"ArnEquals": {"iam:PolicyARN": SUPPLEMENT_POLICY_ARN}},
            ),
        ],
    }
    deletion = {
        "Version": "2012-10-17",
        "Statement": [statement(
            "DeleteExactPilotSupplementOnly",
            ["iam:DeletePolicyVersion", "iam:DeletePolicy"],
            SUPPLEMENT_POLICY_ARN,
        )],
    }
    return {
        "version": "paprnav-pilot-generated-prerequisites-v5",
        "inputs": {"dnsProvider": DNS_PROVIDER, "dnsZoneName": dns_zone_name, "pilotHostname": pilot_hostname, "operatorUpdaterPrincipalArn": updater_principal, "secretsManagerKmsKeyArn": kms_key_arn},
        "baselinePolicyArn": DEPLOY_POLICY_ARN,
        "supplementPolicyArn": SUPPLEMENT_POLICY_ARN,
        "deployRoleArn": DEPLOY_ROLE_ARN,
        "publicationPreconditions": {
            "customerManagedPolicyCharacterLimit": 6144,
            "requiredAvailableRoleAttachmentSlots": 1,
            "requiredAvailablePolicyVersionSlotsWhenExisting": 1,
            "managedPolicyVersionLimit": 5,
        },
        "deployPolicySupplement": {"Version": "2012-10-17", "Statement": deploy_statements},
        "operatorUpdaterProofPolicy": operator,
        "operatorSeparatelyAuthorizedDeletionProofPolicy": deletion,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dns-zone-name", required=True)
    parser.add_argument("--pilot-hostname", required=True)
    parser.add_argument("--operator-updater-principal-arn", required=True)
    parser.add_argument("--secrets-manager-kms-key-arn", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        generated = generate(
            args.dns_zone_name,
            args.pilot_hostname,
            args.operator_updater_principal_arn,
            args.secrets_manager_kms_key_arn,
        )
    except ValueError as exc:
        parser.error(str(exc))
    args.output.write_text(json.dumps(generated, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "pass", "output": str(args.output), "statementCount": len(generated["deployPolicySupplement"]["Statement"])}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
