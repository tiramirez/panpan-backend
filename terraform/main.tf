provider "aws" {
  region  = var.aws_region
}

module "s3_bucket" {
  source = "terraform-aws-modules/s3-bucket/aws"

  bucket = "${var.bucket_name}-${terraform.workspace}"

  versioning = {
    enabled = true
  }

  tags = {
    environment = terraform.workspace
    project     = var.project_name
  }
}

# IAM role for Lambda function
resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role-${terraform.workspace}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    environment = terraform.workspace
    project     = var.project_name
  }
}

# IAM policy for Lambda to access S3
resource "aws_iam_role_policy" "lambda_s3_policy" {
  name = "${var.project_name}-lambda-s3-policy-${terraform.workspace}"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject"
        ]
        Resource = "${module.s3_bucket.s3_bucket_arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# Attach basic Lambda execution policy
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Data source to check if S3 object exists
data "aws_s3_object" "lambda_package" {
  bucket = module.s3_bucket.s3_bucket_id
  key    = "lambda_test.zip"
}

module "lambda_function_from_s3_zip_file" {
  source = "terraform-aws-modules/lambda/aws"

  function_name = "${var.project_name}-lambda-${terraform.workspace}"
  description   = "Test lambda function for ${var.project_name} in ${terraform.workspace}"
  handler       = var.lambda_handler
  runtime       = var.lambda_runtime
  lambda_role   = aws_iam_role.lambda_role.arn

  create_package      = false
  s3_existing_package = {
    bucket = module.s3_bucket.s3_bucket_id
    key    = "lambda_test.zip"
  }

  # Add environment variables if needed
  environment_variables = {
    ENVIRONMENT = terraform.workspace
    PROJECT     = var.project_name
  }

  # Add tags
  tags = {
    environment = terraform.workspace
    project     = var.project_name
  }

  depends_on = [
    module.s3_bucket,
    aws_iam_role_policy.lambda_s3_policy,
    data.aws_s3_object.lambda_package
  ]
}
