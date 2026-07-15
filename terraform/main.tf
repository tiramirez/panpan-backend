provider "aws" {
  region = var.aws_region
}

# ─── Storage ────────────────────────────────────────────────────────────────

resource "aws_dynamodb_table" "orders" {
  name         = "${local.prefix}-orders"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "PK"
  range_key    = "SK"

  attribute {
    name = "PK"
    type = "S"
  }
  attribute {
    name = "SK"
    type = "S"
  }

  tags = {
    environment = local.env
    project     = "panpan"
  }
}

resource "aws_sqs_queue" "orders" {
  name                       = "${local.prefix}-orders"
  visibility_timeout_seconds = 300

  tags = {
    environment = local.env
    project     = "panpan"
  }
}

resource "aws_s3_bucket" "content" {
  bucket = "${local.prefix}-content"

  tags = {
    environment = local.env
    project     = "panpan"
  }
}

resource "aws_s3_bucket_versioning" "content" {
  bucket = aws_s3_bucket.content.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket" "artifacts" {
  bucket = "${local.prefix}-artifacts"

  tags = {
    environment = local.env
    project     = "panpan"
  }
}

resource "aws_s3_bucket_versioning" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  versioning_configuration {
    status = "Enabled"
  }
}

# ─── IAM ────────────────────────────────────────────────────────────────────

resource "aws_iam_role" "lambda_exec" {
  name = "${local.prefix}-lambda-exec"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })

  tags = {
    environment = local.env
    project     = "panpan"
  }
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "${local.prefix}-lambda-policy"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["s3:GetObject", "s3:PutObject"]
        Resource = [
          "${aws_s3_bucket.content.arn}/*",
          "${aws_s3_bucket.artifacts.arn}/*",
        ]
      },
      {
        Effect = "Allow"
        Action = ["s3:ListBucket"]
        Resource = [
          aws_s3_bucket.content.arn,
          aws_s3_bucket.artifacts.arn,
        ]
      },
      {
        Effect   = "Allow"
        Action   = ["sqs:SendMessage", "sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"]
        Resource = aws_sqs_queue.orders.arn
      },
      {
        Effect   = "Allow"
        Action   = ["dynamodb:PutItem", "dynamodb:GetItem", "dynamodb:Query", "dynamodb:UpdateItem"]
        Resource = [aws_dynamodb_table.orders.arn, "${aws_dynamodb_table.orders.arn}/index/*"]
      },
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# ─── Lambda Layer (shared) ───────────────────────────────────────────────────

resource "aws_lambda_layer_version" "shared" {
  layer_name          = "${local.prefix}-shared-layer"
  filename            = "../dist/shared-layer.zip"
  compatible_runtimes = [var.lambda_runtime]

  lifecycle {
    ignore_changes = [filename]
  }
}

# ─── Lambda: api ─────────────────────────────────────────────────────────────

resource "aws_lambda_function" "api" {
  function_name = "${local.prefix}-api"
  role          = aws_iam_role.lambda_exec.arn
  handler       = "handler.lambda_handler"
  runtime       = var.lambda_runtime
  timeout       = 30
  memory_size   = 512

  filename = "../dist/api.zip"

  layers = [aws_lambda_layer_version.shared.arn]

  environment {
    variables = {
      PANPAN_ENV         = local.env
      PANPAN_TABLE_NAME  = aws_dynamodb_table.orders.name
      PANPAN_BUCKET_NAME = aws_s3_bucket.content.id
      PANPAN_QUEUE_URL   = aws_sqs_queue.orders.url
    }
  }

  tags = {
    environment = local.env
    project     = "panpan"
  }

  lifecycle {
    ignore_changes = [filename, source_code_hash]
  }
}

# ─── Lambda: send-email ───────────────────────────────────────────────────────

resource "aws_lambda_function" "send_email" {
  function_name = "${local.prefix}-send-email"
  role          = aws_iam_role.lambda_exec.arn
  handler       = "handler.lambda_handler"
  runtime       = var.lambda_runtime
  timeout       = 60

  filename = "../dist/send-email.zip"

  layers = [aws_lambda_layer_version.shared.arn]

  environment {
    variables = {
      PANPAN_ENV           = local.env
      PANPAN_TABLE_NAME    = aws_dynamodb_table.orders.name
      PANPAN_FROM_EMAIL    = var.panpan_from_email
      PANPAN_GMAIL_PASSWORD = var.panpan_gmail_password
    }
  }

  tags = {
    environment = local.env
    project     = "panpan"
  }

  lifecycle {
    ignore_changes = [filename, source_code_hash]
  }
}

resource "aws_lambda_event_source_mapping" "sqs_to_send_email" {
  event_source_arn = aws_sqs_queue.orders.arn
  function_name    = aws_lambda_function.send_email.arn
  batch_size       = 1
}

# ─── API Gateway ─────────────────────────────────────────────────────────────

resource "aws_apigatewayv2_api" "main" {
  name          = "${local.prefix}-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "OPTIONS"]
    allow_headers = ["Content-Type"]
  }

  tags = {
    environment = local.env
    project     = "panpan"
  }
}

resource "aws_apigatewayv2_integration" "api_lambda" {
  api_id                 = aws_apigatewayv2_api.main.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.api.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "proxy" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.api_lambda.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = "$default"
  auto_deploy = true

  tags = {
    environment = local.env
    project     = "panpan"
  }
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

# ─── CloudWatch: Log Groups ───────────────────────────────────────────────────

resource "aws_cloudwatch_log_group" "api" {
  name              = "/aws/lambda/${aws_lambda_function.api.function_name}"
  retention_in_days = 30

  tags = {
    environment = local.env
    project     = "panpan"
  }
}

resource "aws_cloudwatch_log_group" "send_email" {
  name              = "/aws/lambda/${aws_lambda_function.send_email.function_name}"
  retention_in_days = 30

  tags = {
    environment = local.env
    project     = "panpan"
  }
}

# ─── CloudWatch: Metric Filters ───────────────────────────────────────────────

locals {
  metric_namespace = "Panpan/${local.env}"
}

resource "aws_cloudwatch_log_metric_filter" "menu_queried" {
  name           = "${local.prefix}-menu-queried"
  pattern        = "{ $.event = \"menu_queried\" }"
  log_group_name = aws_cloudwatch_log_group.api.name

  metric_transformation {
    name          = "MenuQueried"
    namespace     = local.metric_namespace
    value         = "1"
    default_value = "0"
  }
}

resource "aws_cloudwatch_log_metric_filter" "checkout_completed" {
  name           = "${local.prefix}-checkout-completed"
  pattern        = "{ $.event = \"checkout_completed\" }"
  log_group_name = aws_cloudwatch_log_group.api.name

  metric_transformation {
    name          = "CheckoutCompleted"
    namespace     = local.metric_namespace
    value         = "1"
    default_value = "0"
  }
}

resource "aws_cloudwatch_log_metric_filter" "checkout_rejected" {
  name           = "${local.prefix}-checkout-rejected"
  pattern        = "{ $.event = \"checkout_rejected\" }"
  log_group_name = aws_cloudwatch_log_group.api.name

  metric_transformation {
    name          = "CheckoutRejected"
    namespace     = local.metric_namespace
    value         = "1"
    default_value = "0"
  }
}

resource "aws_cloudwatch_log_metric_filter" "checkout_error" {
  name           = "${local.prefix}-checkout-error"
  pattern        = "{ $.event = \"checkout_error\" }"
  log_group_name = aws_cloudwatch_log_group.api.name

  metric_transformation {
    name          = "CheckoutError"
    namespace     = local.metric_namespace
    value         = "1"
    default_value = "0"
  }
}

resource "aws_cloudwatch_log_metric_filter" "device_registered" {
  name           = "${local.prefix}-device-registered"
  pattern        = "{ $.event = \"device_registered\" }"
  log_group_name = aws_cloudwatch_log_group.api.name

  metric_transformation {
    name          = "DeviceRegistered"
    namespace     = local.metric_namespace
    value         = "1"
    default_value = "0"
  }
}

resource "aws_cloudwatch_log_metric_filter" "order_saved" {
  name           = "${local.prefix}-order-saved"
  pattern        = "{ $.event = \"order_saved\" }"
  log_group_name = aws_cloudwatch_log_group.send_email.name

  metric_transformation {
    name          = "OrderSaved"
    namespace     = local.metric_namespace
    value         = "1"
    default_value = "0"
  }
}

resource "aws_cloudwatch_log_metric_filter" "email_sent" {
  name           = "${local.prefix}-email-sent"
  pattern        = "{ $.event = \"email_sent\" }"
  log_group_name = aws_cloudwatch_log_group.send_email.name

  metric_transformation {
    name          = "EmailSent"
    namespace     = local.metric_namespace
    value         = "1"
    default_value = "0"
  }
}

resource "aws_cloudwatch_log_metric_filter" "email_failed" {
  name           = "${local.prefix}-email-failed"
  pattern        = "{ $.event = \"email_failed\" }"
  log_group_name = aws_cloudwatch_log_group.send_email.name

  metric_transformation {
    name          = "EmailFailed"
    namespace     = local.metric_namespace
    value         = "1"
    default_value = "0"
  }
}

# ─── CloudWatch: Dashboard ────────────────────────────────────────────────────

resource "aws_cloudwatch_dashboard" "panpan" {
  dashboard_name = "${local.prefix}-operations"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title   = "Orders per hour"
          view    = "bar"
          stat    = "Sum"
          period  = 3600
          metrics = [
            [local.metric_namespace, "CheckoutCompleted", { label = "Completed" }],
            [local.metric_namespace, "CheckoutRejected", { label = "Rejected (store closed)", color = "#FF9900" }],
            [local.metric_namespace, "CheckoutError", { label = "Errors", color = "#D62728" }],
          ]
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          title   = "Order funnel (last 24h)"
          view    = "singleValue"
          stat    = "Sum"
          period  = 86400
          metrics = [
            [local.metric_namespace, "CheckoutCompleted", { label = "Checkouts" }],
            [local.metric_namespace, "OrderSaved", { label = "Saved to DB" }],
            [local.metric_namespace, "EmailSent", { label = "Emails sent" }],
          ]
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        properties = {
          title   = "Errors & failures"
          view    = "timeSeries"
          stat    = "Sum"
          period  = 3600
          metrics = [
            [local.metric_namespace, "CheckoutError", { label = "Checkout error", color = "#D62728" }],
            [local.metric_namespace, "EmailFailed", { label = "Email failed", color = "#FF9900" }],
          ]
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6
        properties = {
          title   = "Menu traffic"
          view    = "timeSeries"
          stat    = "Sum"
          period  = 3600
          metrics = [
            [local.metric_namespace, "MenuQueried", { label = "Menu views" }],
          ]
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 12
        width  = 12
        height = 6
        properties = {
          title   = "Device registrations (experiment)"
          view    = "timeSeries"
          stat    = "Sum"
          period  = 3600
          metrics = [
            [local.metric_namespace, "DeviceRegistered", { label = "Registrations" }],
          ]
        }
      },
    ]
  })
}
