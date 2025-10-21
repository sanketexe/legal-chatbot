#!/usr/bin/env pwsh

# AWS Deployment Script for LegalCounsel AI
# This script automates the deployment process to AWS

param(
    [string]$ProjectName = "legal-chatbot",
    [string]$AWSRegion = "us-east-1",
    [string]$DBPassword,
    [string]$JWTSecret,
    [string]$GeminiAPIKey
)

# Colors for output
$Red = "`e[31m"
$Green = "`e[32m"
$Yellow = "`e[33m"
$Blue = "`e[34m"
$Reset = "`e[0m"

function Write-Status {
    param([string]$Message)
    Write-Host "${Blue}[INFO]${Reset} $Message"
}

function Write-Success {
    param([string]$Message)
    Write-Host "${Green}[SUCCESS]${Reset} $Message"
}

function Write-Warning {
    param([string]$Message)
    Write-Host "${Yellow}[WARNING]${Reset} $Message"
}

function Write-Error {
    param([string]$Message)
    Write-Host "${Red}[ERROR]${Reset} $Message"
}

Write-Host "${Blue}🚀 AWS Deployment Script for LegalCounsel AI${Reset}"
Write-Host "================================================="

# Check prerequisites
Write-Status "Checking prerequisites..."

# Check AWS CLI
try {
    $awsVersion = aws --version
    Write-Success "AWS CLI is installed: $($awsVersion.Split(' ')[0])"
} catch {
    Write-Error "AWS CLI is not installed. Please install it first."
    exit 1
}

# Check Docker
try {
    $dockerVersion = docker --version
    Write-Success "Docker is installed: $($dockerVersion.Split(' ')[2])"
} catch {
    Write-Error "Docker is not installed. Please install Docker Desktop first."
    exit 1
}

# Check AWS credentials
try {
    $identity = aws sts get-caller-identity --output json | ConvertFrom-Json
    Write-Success "AWS credentials configured for account: $($identity.Account)"
} catch {
    Write-Error "AWS credentials not configured. Run: aws configure"
    exit 1
}

# Get required parameters
if (-not $DBPassword) {
    $DBPassword = Read-Host "Enter database password (min 8 characters)" -AsSecureString
    $DBPassword = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($DBPassword))
}

if (-not $JWTSecret) {
    $JWTSecret = Read-Host "Enter JWT secret key"
}

if (-not $GeminiAPIKey) {
    $GeminiAPIKey = Read-Host "Enter Gemini API key"
}

Write-Status "Starting deployment process..."

# Step 1: Create production requirements.txt
Write-Status "Creating production requirements.txt..."
@"
Flask==2.3.3
Flask-CORS==4.0.0
Flask-SQLAlchemy==3.0.5
Flask-JWT-Extended==4.5.2
psycopg2-binary==2.9.7
SQLAlchemy==2.0.21
Werkzeug==2.3.7
cryptography==41.0.4
google-generativeai==0.3.0
python-dotenv==1.0.0
requests==2.31.0
PyJWT==2.8.0
gunicorn==21.2.0
"@ | Out-File -FilePath "requirements.txt" -Encoding UTF8
Write-Success "Requirements.txt created"

# Step 2: Create Dockerfile
Write-Status "Creating Dockerfile..."
@"
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--timeout", "300", "app_with_db:app"]
"@ | Out-File -FilePath "Dockerfile" -Encoding UTF8
Write-Success "Dockerfile created"

# Step 3: Create ECR repository
Write-Status "Creating ECR repository..."
try {
    aws ecr create-repository --repository-name $ProjectName --region $AWSRegion | Out-Null
    Write-Success "ECR repository created: $ProjectName"
} catch {
    Write-Warning "ECR repository may already exist"
}

# Step 4: Get AWS account ID
$AccountId = aws sts get-caller-identity --query Account --output text
Write-Success "AWS Account ID: $AccountId"

# Step 5: Login to ECR
Write-Status "Logging into ECR..."
$loginToken = aws ecr get-login-password --region $AWSRegion
$loginToken | docker login --username AWS --password-stdin "$AccountId.dkr.ecr.$AWSRegion.amazonaws.com"
Write-Success "Logged into ECR"

# Step 6: Build Docker image
Write-Status "Building Docker image..."
docker build -t $ProjectName .
if ($LASTEXITCODE -eq 0) {
    Write-Success "Docker image built successfully"
} else {
    Write-Error "Docker build failed"
    exit 1
}

# Step 7: Tag and push image
Write-Status "Tagging and pushing image to ECR..."
$imageUri = "$AccountId.dkr.ecr.$AWSRegion.amazonaws.com/$ProjectName`:latest"
docker tag "$ProjectName`:latest" $imageUri
docker push $imageUri
if ($LASTEXITCODE -eq 0) {
    Write-Success "Image pushed to ECR: $imageUri"
} else {
    Write-Error "Image push failed"
    exit 1
}

# Step 8: Create RDS database (if not exists)
Write-Status "Creating RDS PostgreSQL database..."
try {
    aws rds create-db-instance `
        --db-instance-identifier "$ProjectName-db" `
        --db-instance-class db.t3.micro `
        --engine postgres `
        --engine-version 15.4 `
        --master-username legaladmin `
        --master-user-password $DBPassword `
        --allocated-storage 20 `
        --storage-type gp2 `
        --publicly-accessible `
        --backup-retention-period 7 `
        --storage-encrypted `
        --region $AWSRegion | Out-Null
    
    Write-Success "RDS database creation initiated"
    Write-Warning "Database creation takes 5-10 minutes..."
    
    # Wait for database
    Write-Status "Waiting for database to become available..."
    aws rds wait db-instance-available --db-instance-identifier "$ProjectName-db" --region $AWSRegion
    Write-Success "Database is now available"
} catch {
    Write-Warning "Database may already exist"
}

# Step 9: Get database endpoint
$dbEndpoint = aws rds describe-db-instances `
    --db-instance-identifier "$ProjectName-db" `
    --query 'DBInstances[0].Endpoint.Address' `
    --output text `
    --region $AWSRegion

Write-Success "Database endpoint: $dbEndpoint"

# Step 10: Create apprunner.yaml
Write-Status "Creating App Runner configuration..."
$databaseUrl = "postgresql://legaladmin:$DBPassword@$dbEndpoint:5432/legalchatbot"

@"
version: 1.0
runtime: docker
build:
  commands:
    build:
      - echo "Building Docker image"
run:
  runtime-version: latest
  command: gunicorn --bind 0.0.0.0:8080 --timeout 300 app_with_db:app
  network:
    port: 8080
    env: PORT
  env:
    - name: FLASK_ENV
      value: production
    - name: DATABASE_URL
      value: $databaseUrl
    - name: JWT_SECRET_KEY
      value: $JWTSecret
    - name: GEMINI_API_KEY
      value: $GeminiAPIKey
"@ | Out-File -FilePath "apprunner.yaml" -Encoding UTF8
Write-Success "App Runner configuration created"

# Final instructions
Write-Host ""
Write-Host "${Green}🎉 Deployment preparation complete!${Reset}"
Write-Host "================================================="
Write-Host ""
Write-Host "${Blue}📋 Next Steps:${Reset}"
Write-Host "1. Go to AWS App Runner Console: https://console.aws.amazon.com/apprunner/"
Write-Host "2. Click 'Create service'"
Write-Host "3. Choose 'Container registry'"
Write-Host "4. Select ECR and use this image URI:"
Write-Host "   ${Yellow}$imageUri${Reset}"
Write-Host "5. Use the apprunner.yaml file for configuration"
Write-Host ""
Write-Host "${Blue}📊 Resources Created:${Reset}"
Write-Host "- ECR Repository: $ProjectName"
Write-Host "- Docker Image: $imageUri"
Write-Host "- RDS Database: $ProjectName-db"
Write-Host "- Database Endpoint: $dbEndpoint"
Write-Host ""
Write-Host "${Blue}🔐 Important Information:${Reset}"
Write-Host "- Database URL: $databaseUrl"
Write-Host "- Save your credentials securely!"
Write-Host ""
Write-Success "Your LegalCounsel AI is ready for AWS deployment! 🚀"