variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "lambda_runtime" {
  description = "Lambda runtime"
  type        = string
  default     = "python3.12"
}

variable "panpan_from_email" {
  description = "From address for confirmation emails"
  type        = string
  default     = "pandemicpantrywest@gmail.com"
}

variable "panpan_gmail_password" {
  description = "Gmail app password for SMTP"
  type        = string
  sensitive   = true
  default     = ""
}
