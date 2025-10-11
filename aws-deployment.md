# AWS Deployment Scripts for LegalAssist Pro

## Option 1: AWS App Runner (Recommended - Easiest)
# Simple container-based deployment with automatic scaling

# 1. Install AWS CLI
# Windows: https://aws.amazon.com/cli/
# Or use: winget install -e --id Amazon.AWSCLI

# 2. Configure AWS CLI
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key  
# Enter your region (e.g., us-east-1, us-west-2, eu-west-1)
# Enter output format: json

# 3. Create ECR Repository
aws ecr create-repository --repository-name legal-chatbot --region us-east-1

# 4. Get ECR login token
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <your-account-id>.dkr.ecr.us-east-1.amazonaws.com

# 5. Build and tag Docker image
docker build -t legal-chatbot .
docker tag legal-chatbot:latest <your-account-id>.dkr.ecr.us-east-1.amazonaws.com/legal-chatbot:latest

# 6. Push to ECR
docker push <your-account-id>.dkr.ecr.us-east-1.amazonaws.com/legal-chatbot:latest

# 7. Create App Runner service (via AWS Console)
# - Go to AWS App Runner console
# - Create service
# - Choose "Container registry" 
# - Select your ECR image
# - Configure environment variables: GEMINI_API_KEY
# - Deploy!

## Option 2: AWS ECS with Fargate (More Advanced)
# For production workloads with more control

# 1. Create ECS cluster
aws ecs create-cluster --cluster-name legal-chatbot-cluster

# 2. Create task definition
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json

# 3. Create ECS service
aws ecs create-service \
  --cluster legal-chatbot-cluster \
  --service-name legal-chatbot-service \
  --task-definition legal-chatbot-task \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345],securityGroups=[sg-12345],assignPublicIp=ENABLED}"

## Option 3: AWS Lambda (Serverless)
# For cost-effective, pay-per-request deployment

# 1. Install AWS SAM CLI
# 2. Use sam init for serverless template
# 3. Deploy with sam deploy

## Environment Variables Needed:
# GEMINI_API_KEY=your_google_gemini_api_key

## Expected AWS Costs:
# App Runner: ~$25-50/month for small traffic
# ECS Fargate: ~$15-30/month for single instance
# Lambda: ~$5-15/month for moderate usage

## Security Notes:
# - Use IAM roles, not access keys in production
# - Store API keys in AWS Secrets Manager
# - Enable CloudWatch logging
# - Set up ALB with SSL certificate