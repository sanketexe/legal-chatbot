# AWS RDS PostgreSQL Setup Script for LegalCounsel AI (PowerShell)
# Run this script to create AWS RDS database for your chatbot

param(
    [string]$DBInstanceClass = "db.t3.micro",
    [string]$StorageSize = "20",
    [string]$AWSRegion = "us-east-1"
)

# Configuration
$DBInstanceId = "legal-chatbot-db"
$DBName = "legalchatbot"
$DBUsername = "legaladmin"
$DBPassword = ""

Write-Host "🗄️  Setting up AWS RDS PostgreSQL for LegalCounsel AI" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

# Function to print colored output
function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Check if AWS CLI is installed
try {
    aws --version | Out-Null
    Write-Success "AWS CLI is installed"
} catch {
    Write-Error "AWS CLI is not installed. Please install it first:"
    Write-Host "  Run: winget install -e --id Amazon.AWSCLI"
    exit 1
}

# Check AWS credentials
Write-Status "Checking AWS credentials..."
try {
    aws sts get-caller-identity | Out-Null
    Write-Success "AWS credentials verified"
} catch {
    Write-Error "AWS credentials not configured. Run: aws configure"
    exit 1
}

# Get database password
do {
    $SecurePassword = Read-Host "Enter a secure database password (min 8 characters)" -AsSecureString
    $DBPassword = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecurePassword))
    
    if ($DBPassword.Length -lt 8) {
        Write-Warning "Password must be at least 8 characters"
        $DBPassword = ""
    }
} while ($DBPassword -eq "")

# Get default VPC and subnets
Write-Status "Getting default VPC and security group..."

$DefaultVPC = aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query 'Vpcs[0].VpcId' --output text --region $AWSRegion
if ($DefaultVPC -eq "None") {
    Write-Error "No default VPC found. Please create a VPC first."
    exit 1
}

$DefaultSG = aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$DefaultVPC" "Name=group-name,Values=default" --query 'SecurityGroups[0].GroupId' --output text --region $AWSRegion

Write-Success "Using VPC: $DefaultVPC, Security Group: $DefaultSG"

# Create RDS subnet group
Write-Status "Creating RDS subnet group..."

$Subnets = aws ec2 describe-subnets --filters "Name=vpc-id,Values=$DefaultVPC" --query 'Subnets[].SubnetId' --output text --region $AWSRegion
$SubnetArray = $Subnets -split '\s+'

if ($SubnetArray.Count -lt 2) {
    Write-Error "Need at least 2 subnets for RDS. Found only $($SubnetArray.Count)"
    exit 1
}

try {
    aws rds create-db-subnet-group `
        --db-subnet-group-name legal-chatbot-subnet-group `
        --db-subnet-group-description "Subnet group for Legal Chatbot RDS" `
        --subnet-ids $SubnetArray[0] $SubnetArray[1] `
        --region $AWSRegion 2>$null
} catch {
    Write-Warning "Subnet group may already exist"
}

# Update security group to allow PostgreSQL access
Write-Status "Updating security group for PostgreSQL access..."

try {
    aws ec2 authorize-security-group-ingress `
        --group-id $DefaultSG `
        --protocol tcp `
        --port 5432 `
        --source-group $DefaultSG `
        --region $AWSRegion 2>$null
} catch {
    Write-Warning "Security group rule may already exist"
}

# Create RDS instance
Write-Status "Creating RDS PostgreSQL instance..."
Write-Warning "This will take 5-10 minutes. Please wait..."

aws rds create-db-instance `
    --db-instance-identifier $DBInstanceId `
    --db-instance-class $DBInstanceClass `
    --engine postgres `
    --engine-version 15.4 `
    --master-username $DBUsername `
    --master-user-password "$DBPassword" `
    --allocated-storage $StorageSize `
    --storage-type gp2 `
    --vpc-security-group-ids $DefaultSG `
    --db-subnet-group-name legal-chatbot-subnet-group `
    --backup-retention-period 7 `
    --storage-encrypted `
    --publicly-accessible `
    --region $AWSRegion

# Wait for database to be available
Write-Status "Waiting for database to become available..."

aws rds wait db-instance-available `
    --db-instance-identifier $DBInstanceId `
    --region $AWSRegion

# Get database endpoint
$DBEndpoint = aws rds describe-db-instances `
    --db-instance-identifier $DBInstanceId `
    --query 'DBInstances[0].Endpoint.Address' `
    --output text `
    --region $AWSRegion

Write-Success "Database created successfully!"
Write-Host ""
Write-Host "📊 Database Information:" -ForegroundColor Cyan
Write-Host "========================" -ForegroundColor Cyan
Write-Host "Endpoint: $DBEndpoint"
Write-Host "Port: 5432"
Write-Host "Database: $DBName"
Write-Host "Username: $DBUsername"
Write-Host "Instance Class: $DBInstanceClass"
Write-Host "Storage: ${StorageSize}GB"
Write-Host ""
Write-Host "🔗 Connection String:" -ForegroundColor Cyan
Write-Host "postgresql://$DBUsername`:$DBPassword@$DBEndpoint`:5432/$DBName"
Write-Host ""
Write-Host "📝 Environment Variables for your app:" -ForegroundColor Cyan
Write-Host "DATABASE_URL=postgresql://$DBUsername`:$DBPassword@$DBEndpoint`:5432/$DBName"
Write-Host ""
Write-Success "Setup complete! Your AWS RDS PostgreSQL database is ready."
Write-Warning "Remember to update your application's environment variables."

# Clear password from memory
$DBPassword = $null
$SecurePassword = $null