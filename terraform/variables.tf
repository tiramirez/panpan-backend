variable "bucket_name" {
  description = "Base name of the S3 bucket to store artifacts."
  type        = string
}

variable "project_name" {
  description = "Projects name use for tags"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "lambda_handler" {
  description = "Lambda function handler"
  type        = string
  default     = "handler.lambda_handler"
}

variable "lambda_runtime" {
  description = "Lambda runtime"
  type        = string
  default     = "python3.11"
}
