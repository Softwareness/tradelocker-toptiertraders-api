variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-1"
}

variable "aws_profile" {
  description = "AWS profile to use"
  type        = string
  default     = "landingzone"
}

variable "app_name" {
  description = "Name of the App Runner service"
  type        = string
  default     = "tradelocker-api"
}

variable "github_repository_url" {
  description = "GitHub repository URL"
  type        = string
  default     = "https://github.com/Softwareness/tradelocker-api"
}

variable "github_token" {
  description = "GitHub personal access token for private repository access"
  type        = string
  default     = ""
  sensitive   = true
}

variable "is_private_repository" {
  description = "Whether the GitHub repository is private"
  type        = bool
  default     = false
}

variable "source_branch" {
  description = "GitHub branch to deploy"
  type        = string
  default     = "main"
}

variable "auto_deployments_enabled" {
  description = "Enable automatic deployments"
  type        = bool
  default     = true
}

variable "instance_cpu" {
  description = "CPU units for the App Runner instance"
  type        = string
  default     = "1 vCPU"
}

variable "instance_memory" {
  description = "Memory for the App Runner instance"
  type        = string
  default     = "2 GB"
}

variable "max_concurrency" {
  description = "Maximum number of concurrent requests"
  type        = number
  default     = 50
}

variable "max_size" {
  description = "Maximum number of instances"
  type        = number
  default     = 10
}

variable "min_size" {
  description = "Minimum number of instances"
  type        = number
  default     = 1
}

variable "secrets_manager_arn" {
  description = "ARN of the Secrets Manager secret for TradeLocker credentials"
  type        = string
  default     = "arn:aws:secretsmanager:eu-west-1:491649323445:secret:tradelocker/credentials"
}

variable "dynamodb_table_arn" {
  description = "ARN of the DynamoDB table for order logging"
  type        = string
  default     = "arn:aws:dynamodb:eu-west-1:491649323445:table/tradelocker-orders"
}

variable "api_key" {
  description = "API key for securing the endpoints"
  type        = string
  default     = "your-secret-api-key-here"
  sensitive   = true
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default = {
    Environment = "production"
    Project     = "tradelocker-api"
    ManagedBy   = "terraform"
  }
} 