terraform {
  required_version = ">= 1.11.0"

  backend "s3" {
    bucket       = "paprnav-pilot-terraform-state-527257972989"
    key          = "pilot/terraform.tfstate"
    region       = "us-east-1"
    profile      = "paprnav-deploy"
    encrypt      = true
    use_lockfile = true
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile

  allowed_account_ids = [var.aws_account_id]

  default_tags {
    tags = local.common_tags
  }
}
