output "api_gateway_url" {
  description = "Base URL for the API Gateway"
  value       = aws_apigatewayv2_stage.default.invoke_url
}

output "api_lambda_function_name" {
  description = "Name of the API Lambda function"
  value       = aws_lambda_function.api.function_name
}

output "send_email_lambda_function_name" {
  description = "Name of the send-email Lambda function"
  value       = aws_lambda_function.send_email.function_name
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB orders table"
  value       = aws_dynamodb_table.orders.name
}

output "sqs_queue_url" {
  description = "URL of the orders SQS queue"
  value       = aws_sqs_queue.orders.url
}

output "content_bucket_name" {
  description = "Name of the content S3 bucket"
  value       = aws_s3_bucket.content.id
}

output "artifacts_bucket_name" {
  description = "Name of the artifacts S3 bucket"
  value       = aws_s3_bucket.artifacts.id
}
