terraform {
  backend "s3" {
    bucket  = "panpan-terraform-state"
    region  = "us-east-1"
    key     = "terraform/dev/terraform.tfstate"
    encrypt = true
  }

  required_version = ">=1.5.0"
  required_providers {
    aws = {
      version = ">= 5.0"
      source  = "hashicorp/aws"
    }
  }
}
