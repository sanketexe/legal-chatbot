#!/bin/bash

# AWS RDS PostgreSQL Setup Script for LegalCounsel AI
# Run this script to create AWS RDS database for your chatbot

set -e

echo "🗄️  Setting up AWS RDS PostgreSQL for LegalCounsel AI"
echo "================================================="

# Configuration
DB_INSTANCE_ID="legal-chatbot-db"
DB_NAME="legalchatbot"
DB_USERNAME="legaladmin"
DB_PASSWORD=""
DB_INSTANCE_CLASS="db.t3.micro"
STORAGE_SIZE="20"
AWS_REGION="us-east-1"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed. Please install it first:"
    echo "  - Windows: winget install -e --id Amazon.AWSCLI"
    echo "  - macOS: brew install awscli"
    echo "  - Linux: https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2-linux.html"
    exit 1
fi

# Check AWS credentials
print_status "Checking AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    print_error "AWS credentials not configured. Run: aws configure"
    exit 1
fi

print_success "AWS credentials verified"

# Get database password
while [[ -z "$DB_PASSWORD" ]]; do
    echo -n "Enter a secure database password (min 8 characters): "
    read -s DB_PASSWORD
    echo
    if [[ ${#DB_PASSWORD} -lt 8 ]]; then
        print_warning "Password must be at least 8 characters"
        DB_PASSWORD=""
    fi
done

# Get default VPC and subnets
print_status "Getting default VPC and security group..."

DEFAULT_VPC=$(aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query 'Vpcs[0].VpcId' --output text --region $AWS_REGION)
if [[ "$DEFAULT_VPC" == "None" ]]; then
    print_error "No default VPC found. Please create a VPC first."
    exit 1
fi

DEFAULT_SG=$(aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$DEFAULT_VPC" "Name=group-name,Values=default" --query 'SecurityGroups[0].GroupId' --output text --region $AWS_REGION)

print_success "Using VPC: $DEFAULT_VPC, Security Group: $DEFAULT_SG"

# Create RDS subnet group
print_status "Creating RDS subnet group..."

SUBNETS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$DEFAULT_VPC" --query 'Subnets[].SubnetId' --output text --region $AWS_REGION)
SUBNET_ARRAY=($SUBNETS)

if [[ ${#SUBNET_ARRAY[@]} -lt 2 ]]; then
    print_error "Need at least 2 subnets for RDS. Found only ${#SUBNET_ARRAY[@]}"
    exit 1
fi

aws rds create-db-subnet-group \
    --db-subnet-group-name legal-chatbot-subnet-group \
    --db-subnet-group-description "Subnet group for Legal Chatbot RDS" \
    --subnet-ids ${SUBNET_ARRAY[0]} ${SUBNET_ARRAY[1]} \
    --region $AWS_REGION 2>/dev/null || print_warning "Subnet group may already exist"

# Update security group to allow PostgreSQL access
print_status "Updating security group for PostgreSQL access..."

aws ec2 authorize-security-group-ingress \
    --group-id $DEFAULT_SG \
    --protocol tcp \
    --port 5432 \
    --source-group $DEFAULT_SG \
    --region $AWS_REGION 2>/dev/null || print_warning "Security group rule may already exist"

# Create RDS instance
print_status "Creating RDS PostgreSQL instance..."
print_warning "This will take 5-10 minutes. Please wait..."

aws rds create-db-instance \
    --db-instance-identifier $DB_INSTANCE_ID \
    --db-instance-class $DB_INSTANCE_CLASS \
    --engine postgres \
    --engine-version 15.4 \
    --master-username $DB_USERNAME \
    --master-user-password "$DB_PASSWORD" \
    --allocated-storage $STORAGE_SIZE \
    --storage-type gp2 \
    --vpc-security-group-ids $DEFAULT_SG \
    --db-subnet-group-name legal-chatbot-subnet-group \
    --backup-retention-period 7 \
    --storage-encrypted \
    --publicly-accessible \
    --region $AWS_REGION

# Wait for database to be available
print_status "Waiting for database to become available..."

aws rds wait db-instance-available \
    --db-instance-identifier $DB_INSTANCE_ID \
    --region $AWS_REGION

# Get database endpoint
DB_ENDPOINT=$(aws rds describe-db-instances \
    --db-instance-identifier $DB_INSTANCE_ID \
    --query 'DBInstances[0].Endpoint.Address' \
    --output text \
    --region $AWS_REGION)

print_success "Database created successfully!"
echo
echo "📊 Database Information:"
echo "========================"
echo "Endpoint: $DB_ENDPOINT"
echo "Port: 5432"
echo "Database: $DB_NAME"
echo "Username: $DB_USERNAME"
echo "Instance Class: $DB_INSTANCE_CLASS"
echo "Storage: ${STORAGE_SIZE}GB"
echo
echo "🔗 Connection String:"
echo "postgresql://$DB_USERNAME:$DB_PASSWORD@$DB_ENDPOINT:5432/$DB_NAME"
echo
echo "📝 Environment Variables for your app:"
echo "DATABASE_URL=postgresql://$DB_USERNAME:$DB_PASSWORD@$DB_ENDPOINT:5432/$DB_NAME"
echo
print_success "Setup complete! Your AWS RDS PostgreSQL database is ready."
print_warning "Remember to update your application's environment variables."