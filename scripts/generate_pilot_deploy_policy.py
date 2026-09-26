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
ZONE_RE = re.compile(r"^Z[A-Z0-9]{8,32}$")
PRINCIPAL_RE = re.compile(rf"^arn:aws:iam::{ACCOUNT}:(?:user|role)/[^\s]+$")
KMS_RE = re.compile(rf"^arn:aws:kms:{REGION}:{ACCOUNT}:key/[0-9a-f-]+$")
HOSTNAME_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)+$")


def statement(sid: str, actions: list[str], resource: str | list[str], condition: dict[str, Any] | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"Sid": sid, "Effect": "Allow", "Action": actions, "Resource": resource}
    if condition:
        result["Condition"] = condition
    return result


def generate(zone_id: str, pilot_hostname: str, updater_principal: str, kms_key_arn: str) -> dict[str, Any]:
    if ZONE_RE.fullmatch(zone_id) is None:
        raise ValueError("invalid Route53 zone ID")
    if HOSTNAME_RE.fullmatch(pilot_hostname) is None:
        raise ValueError("pilot hostname must be one canonical lower-case DNS hostname")
    if PRINCIPAL_RE.fullmatch(updater_principal) is None:
        raise ValueError("updater principal must be an exact account IAM user or role ARN")
    if KMS_RE.fullmatch(kms_key_arn) is None:
        raise ValueError("Secrets Manager KMS key must be one exact account/region key ARN")
    service_roles = {
        "rds.amazonaws.com": f"arn:aws:iam::{ACCOUNT}:role/aws-service-role/rds.amazonaws.com/AWSServiceRoleForRDS",
        "ecs.amazonaws.com": f"arn:aws:iam::{ACCOUNT}:role/aws-service-role/ecs.amazonaws.com/AWSServiceRoleForECS",
        "elasticloadbalancing.amazonaws.com": f"arn:aws:iam::{ACCOUNT}:role/aws-service-role/elasticloadbalancing.amazonaws.com/AWSServiceRoleForElasticLoadBalancing",
    }
    deploy_statements = [
        statement(
            "AcmListCertificates",
            ["acm:ListCertificates"],
            "*",
            {"StringEquals": {"aws:RequestedRegion": REGION}},
        ),
        statement(
            "AcmReadCertificateMetadata",
            ["acm:DescribeCertificate", "acm:ListTagsForCertificate", "acm:GetCertificate"],
            f"arn:aws:acm:{REGION}:{ACCOUNT}:certificate/*",
            {"StringEquals": {"aws:RequestedRegion": REGION}},
        ),
        statement("WafInventory", ["wafv2:ListWebACLs", "wafv2:ListRegexPatternSets", "wafv2:GetWebACLForResource"], "*"),
        statement(
            "WafCreateTaggedPilotResources",
            ["wafv2:CreateWebACL", "wafv2:CreateRegexPatternSet"],
            "*",
            {"StringEquals": {"aws:RequestTag/Project": "paprnav", "aws:RequestedRegion": REGION}},
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
            [f"arn:aws:wafv2:{REGION}:{ACCOUNT}:regional/webacl/paprnav-*/*", f"arn:aws:elasticloadbalancing:{REGION}:{ACCOUNT}:loadbalancer/app/paprnav-*/*"],
        ),
        statement("Route53Inventory", ["route53:ListHostedZones", "route53:GetChange"], "*"),
        statement(
            "Route53ReadExactPilotZone",
            ["route53:GetHostedZone", "route53:ListResourceRecordSets", "route53:ListTagsForResource"],
            f"arn:aws:route53:::hostedzone/{zone_id}",
        ),
        statement(
            "Route53ChangeExactPilotAlias",
            ["route53:ChangeResourceRecordSets"],
            f"arn:aws:route53:::hostedzone/{zone_id}",
            {
                "ForAllValues:StringEquals": {
                    "route53:ChangeResourceRecordSetsNormalizedRecordNames": [pilot_hostname],
                    "route53:ChangeResourceRecordSetsRecordTypes": ["A"],
                    "route53:ChangeResourceRecordSetsActions": ["CREATE", "UPSERT", "DELETE"],
                }
            },
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
        ),
        statement(
            "PassExactWorkerSchedulerRole",
            ["iam:PassRole"],
            WORKER_SCHEDULER_ROLE_ARN,
            {"StringEquals": {"iam:PassedToService": "scheduler.amazonaws.com"}},
        ),
        statement(
            "PilotSecretLifecycleWithoutValues",
            ["secretsmanager:CreateSecret", "secretsmanager:DescribeSecret", "secretsmanager:TagResource", "secretsmanager:UntagResource", "secretsmanager:DeleteSecret", "secretsmanager:RestoreSecret", "secretsmanager:PutResourcePolicy", "secretsmanager:GetResourcePolicy", "secretsmanager:DeleteResourcePolicy"],
            f"arn:aws:secretsmanager:{REGION}:{ACCOUNT}:secret:/paprnav/pilot/*",
        ),
        statement(
            "RdsManagedSecretCreation",
            ["secretsmanager:CreateSecret"],
            "*",
            {"StringLike": {"secretsmanager:Name": "rds!db-*"}, "StringEquals": {"aws:RequestedRegion": REGION}},
        ),
        statement(
            "RdsManagedSecretTagging",
            ["secretsmanager:TagResource"],
            f"arn:aws:secretsmanager:{REGION}:{ACCOUNT}:secret:rds!db-*",
        ),
        statement("RdsManagedSecretKmsDescribe", ["kms:DescribeKey"], kms_key_arn),
    ]
    for index, (service_name, role_arn) in enumerate(service_roles.items(), start=1):
        deploy_statements.append(statement(
            f"CreateServiceLinkedRole{index}",
            ["iam:CreateServiceLinkedRole"],
            role_arn,
            {"StringEquals": {"iam:AWSServiceName": service_name}},
        ))
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
        "version": "paprnav-pilot-generated-prerequisites-v3",
        "inputs": {"hostedZoneId": zone_id, "pilotHostname": pilot_hostname, "operatorUpdaterPrincipalArn": updater_principal, "secretsManagerKmsKeyArn": kms_key_arn},
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
    parser.add_argument("--hosted-zone-id", required=True)
    parser.add_argument("--pilot-hostname", required=True)
    parser.add_argument("--operator-updater-principal-arn", required=True)
    parser.add_argument("--secrets-manager-kms-key-arn", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        generated = generate(
            args.hosted_zone_id,
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
