terraform {
  required_version = ">= 1.0"
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
}

# App Runner Service
resource "aws_apprunner_service" "tradelocker_api" {
  service_name = var.app_name

  source_configuration {
    auto_deployments_enabled = var.auto_deployments_enabled

    source_code_version {
      type  = "BRANCH"
      value = var.source_branch
    }

    code_repository {
      code_configuration {
        configuration_source = "API"
        runtime             = "PYTHON_3"
        build_command       = "pip install -r requirements.txt"
        start_command       = "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
      }

      source_code_version {
        type  = "BRANCH"
        value = var.source_branch
      }

      repository_url = var.github_repository_url
    }
  }

  instance_configuration {
    cpu    = var.instance_cpu
    memory = var.instance_memory

    instance_role_arn = aws_iam_role.apprunner_service_role.arn
  }

  auto_scaling_configuration_arn = aws_apprunner_auto_scaling_configuration_version.tradelocker_api.arn

  tags = var.tags
}

# Auto Scaling Configuration
resource "aws_apprunner_auto_scaling_configuration_version" "tradelocker_api" {
  auto_scaling_configuration_name = "${var.app_name}-scaling"
  max_concurrency                 = var.max_concurrency
  max_size                        = var.max_size
  min_size                        = var.min_size

  tags = var.tags
}

# IAM Role for App Runner Service
resource "aws_iam_role" "apprunner_service_role" {
  name = "${var.app_name}-service-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "build.apprunner.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# IAM Role Policy for App Runner Service
resource "aws_iam_role_policy" "apprunner_service_policy" {
  name = "${var.app_name}-service-policy"
  role = aws_iam_role.apprunner_service_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          var.secrets_manager_arn,
          var.dynamodb_table_arn
        ]
      }
    ]
  })
}

# IAM Role for App Runner Instance
resource "aws_iam_role" "apprunner_instance_role" {
  name = "${var.app_name}-instance-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "tasks.apprunner.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# IAM Role Policy for App Runner Instance
resource "aws_iam_role_policy" "apprunner_instance_policy" {
  name = "${var.app_name}-instance-policy"
  role = aws_iam_role.apprunner_instance_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          var.secrets_manager_arn,
          var.dynamodb_table_arn
        ]
      }
    ]
  })
}

# Attach instance role to service
resource "aws_apprunner_service" "tradelocker_api_with_instance_role" {
  service_name = var.app_name

  source_configuration {
    auto_deployments_enabled = var.auto_deployments_enabled

    source_code_version {
      type  = "BRANCH"
      value = var.source_branch
    }

    code_repository {
      code_configuration {
        configuration_source = "API"
        runtime             = "PYTHON_3"
        build_command       = "pip install -r requirements.txt"
        start_command       = "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
      }

      source_code_version {
        type  = "BRANCH"
        value = var.source_branch
      }

      repository_url = var.github_repository_url
    }
  }

  instance_configuration {
    cpu    = var.instance_cpu
    memory = var.instance_memory

    instance_role_arn = aws_iam_role.apprunner_instance_role.arn
  }

  # Environment variables for the service
  environment_variables = {
    API_KEY = var.api_key
  }

  auto_scaling_configuration_arn = aws_apprunner_auto_scaling_configuration_version.tradelocker_api.arn

  tags = var.tags

  depends_on = [aws_apprunner_service.tradelocker_api]
} 