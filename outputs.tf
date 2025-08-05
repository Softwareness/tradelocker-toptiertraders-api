output "app_runner_service_url" {
  description = "URL of the App Runner service"
  value       = aws_apprunner_service.tradelocker_api_with_instance_role.service_url
}

output "app_runner_service_arn" {
  description = "ARN of the App Runner service"
  value       = aws_apprunner_service.tradelocker_api_with_instance_role.arn
}

output "app_runner_service_name" {
  description = "Name of the App Runner service"
  value       = aws_apprunner_service.tradelocker_api_with_instance_role.service_name
}

output "auto_scaling_configuration_arn" {
  description = "ARN of the auto scaling configuration"
  value       = aws_apprunner_auto_scaling_configuration_version.tradelocker_api.arn
}

output "service_role_arn" {
  description = "ARN of the App Runner service role"
  value       = aws_iam_role.apprunner_service_role.arn
}

output "instance_role_arn" {
  description = "ARN of the App Runner instance role"
  value       = aws_iam_role.apprunner_instance_role.arn
}

output "api_endpoints" {
  description = "Available API endpoints"
  value = {
    health_check = "https://${aws_apprunner_service.tradelocker_api_with_instance_role.service_url}/health"
    accounts = "https://${aws_apprunner_service.tradelocker_api_with_instance_role.service_url}/accounts"
    account_details = "https://${aws_apprunner_service.tradelocker_api_with_instance_role.service_url}/accounts/details"
    orders = "https://${aws_apprunner_service.tradelocker_api_with_instance_role.service_url}/orders"
    positions = "https://${aws_apprunner_service.tradelocker_api_with_instance_role.service_url}/positions"
    instruments = "https://${aws_apprunner_service.tradelocker_api_with_instance_role.service_url}/instruments"
    documentation = "https://${aws_apprunner_service.tradelocker_api_with_instance_role.service_url}/docs"
  }
}

output "deployment_instructions" {
  description = "Instructions for deploying the API"
  value = <<-EOT
    🚀 TradeLocker API Deployed Successfully!
    
    📋 Service Information:
    - Service URL: https://${aws_apprunner_service.tradelocker_api_with_instance_role.service_url}
    - Service Name: ${aws_apprunner_service.tradelocker_api_with_instance_role.service_name}
    - Region: ${var.aws_region}
    
    🧪 Test Commands:
    # Health check
    curl https://${aws_apprunner_service.tradelocker_api_with_instance_role.service_url}/health
    
    # Get accounts
    curl https://${aws_apprunner_service.tradelocker_api_with_instance_role.service_url}/accounts
    
    # Get detailed account info
    curl https://${aws_apprunner_service.tradelocker_api_with_instance_role.service_url}/accounts/details
    
    # Get instruments
    curl https://${aws_apprunner_service.tradelocker_api_with_instance_role.service_url}/instruments
    
    # Create order (example)
    curl -X POST https://${aws_apprunner_service.tradelocker_api_with_instance_role.service_url}/orders \\
      -H 'Content-Type: application/json' \\
      -d '{"symbol":"BTCUSD.TTF","order_type":"market","side":"buy","quantity":0.01}'
    
    📚 Documentation:
    - Swagger UI: https://${aws_apprunner_service.tradelocker_api_with_instance_role.service_url}/docs
    - ReDoc: https://${aws_apprunner_service.tradelocker_api_with_instance_role.service_url}/redoc
    
    🔧 Management:
    # View service status
    aws apprunner describe-service --service-name ${aws_apprunner_service.tradelocker_api_with_instance_role.service_name} --region ${var.aws_region} --profile ${var.aws_profile}
    
    # View logs
    aws logs tail /aws/apprunner/${aws_apprunner_service.tradelocker_api_with_instance_role.service_name} --region ${var.aws_region} --profile ${var.aws_profile}
    
    # Delete service
    aws apprunner delete-service --service-name ${aws_apprunner_service.tradelocker_api_with_instance_role.service_name} --region ${var.aws_region} --profile ${var.aws_profile}
  EOT
} 