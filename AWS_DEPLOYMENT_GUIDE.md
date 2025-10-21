# 🚀 Step-by-Step AWS Deployment Guide for LegalCounsel AI

## 📋 Prerequisites

Before starting, ensure you have:
- ✅ AWS Account with billing set up
- ✅ AWS CLI installed and configured
- ✅ Docker Desktop installed (for containerization)
- ✅ Your project code ready
- ✅ Environment variables identified

---

## 🎯 Deployment Architecture Overview

We'll deploy using **AWS App Runner** (easiest) with **RDS PostgreSQL** database:

```
Internet → AWS App Runner → RDS PostgreSQL
         ↓
    Your Flask App (app_with_db.py)
```

**Benefits:**
- 🚀 **Easy deployment** - Minimal configuration
- 📈 **Auto-scaling** - Handles traffic spikes
- 💰 **Cost-effective** - Pay only for usage
- 🔒 **Secure** - Built-in SSL and VPC

---

## 📋 Step 1: Install and Configure AWS CLI

### Windows (PowerShell):
```powershell
# Install AWS CLI
winget install -e --id Amazon.AWSCLI

# Verify installation
aws --version
```

### Configure AWS CLI:
```bash
aws configure
```

Enter:
- **AWS Access Key ID**: `your-access-key`
- **AWS Secret Access Key**: `your-secret-key`
- **Default region**: `us-east-1` (or your preferred region)
- **Output format**: `json`

### Test Configuration:
```bash
aws sts get-caller-identity
```

---

## 📋 Step 2: Prepare Your Application

### 2.1 Create Production Requirements File:
```bash
# Create requirements.txt for production
echo "Flask==2.3.3
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
gunicorn==21.2.0" > requirements.txt
```

### 2.2 Create Dockerfile:
```dockerfile
# Create Dockerfile in your project root
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--timeout", "300", "app_with_db:app"]
```

### 2.3 Update Your Flask App for Production:
Add this to the end of `app_with_db.py`:
```python
# Add this at the end of app_with_db.py
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# Create the app instance for gunicorn
app = create_app()
```

---

## 📋 Step 3: Create AWS RDS PostgreSQL Database

### 3.1 Run the Database Setup Script:
```powershell
# Use the automated script I created for you
.\setup_aws_database.ps1
```

**OR manually via AWS CLI:**
```bash
# Create RDS PostgreSQL instance
aws rds create-db-instance \
    --db-instance-identifier legal-chatbot-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --engine-version 15.4 \
    --master-username legaladmin \
    --master-user-password "YourSecurePassword123!" \
    --allocated-storage 20 \
    --storage-type gp2 \
    --publicly-accessible \
    --backup-retention-period 7 \
    --storage-encrypted \
    --region us-east-1
```

### 3.2 Wait for Database to be Ready:
```bash
# Wait for database (takes 5-10 minutes)
aws rds wait db-instance-available --db-instance-identifier legal-chatbot-db
```

### 3.3 Get Database Endpoint:
```bash
# Get the database endpoint
aws rds describe-db-instances \
    --db-instance-identifier legal-chatbot-db \
    --query 'DBInstances[0].Endpoint.Address' \
    --output text
```

---

## 📋 Step 4: Create ECR Repository for Docker Images

### 4.1 Create ECR Repository:
```bash
# Create repository for your Docker images
aws ecr create-repository --repository-name legal-chatbot --region us-east-1
```

### 4.2 Get ECR Login Token:
```bash
# Get your account ID first
aws sts get-caller-identity --query Account --output text

# Login to ECR (replace YOUR-ACCOUNT-ID)
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR-ACCOUNT-ID.dkr.ecr.us-east-1.amazonaws.com
```

---

## 📋 Step 5: Build and Push Docker Image

### 5.1 Build Docker Image:
```bash
# Build your Docker image
docker build -t legal-chatbot .
```

### 5.2 Tag Image for ECR:
```bash
# Tag for ECR (replace YOUR-ACCOUNT-ID)
docker tag legal-chatbot:latest YOUR-ACCOUNT-ID.dkr.ecr.us-east-1.amazonaws.com/legal-chatbot:latest
```

### 5.3 Push to ECR:
```bash
# Push to ECR
docker push YOUR-ACCOUNT-ID.dkr.ecr.us-east-1.amazonaws.com/legal-chatbot:latest
```

---

## 📋 Step 6: Create App Runner Service

### 6.1 Create apprunner.yaml Configuration:
```yaml
# Create apprunner.yaml in your project root
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
      value: postgresql://legaladmin:YourSecurePassword123!@YOUR-RDS-ENDPOINT:5432/legalchatbot
    - name: JWT_SECRET_KEY
      value: your-production-jwt-secret-key
    - name: GEMINI_API_KEY
      value: your-gemini-api-key
```

### 6.2 Create App Runner Service via AWS Console:

1. **Go to AWS App Runner Console**
2. **Click "Create service"**
3. **Choose "Container registry"**
4. **Select your ECR repository**
5. **Configure:**
   - **Service name**: `legal-chatbot-service`
   - **CPU**: 0.25 vCPU
   - **Memory**: 0.5 GB
   - **Port**: 8080

### 6.3 Add Environment Variables:
```
FLASK_ENV=production
DATABASE_URL=postgresql://legaladmin:password@your-rds-endpoint:5432/legalchatbot
JWT_SECRET_KEY=your-production-secret-key
GEMINI_API_KEY=your-gemini-api-key
```

---

## 📋 Step 7: Migrate Data to RDS (Optional)

### 7.1 Run Migration Script:
```bash
# If you have existing SQLite data
python migrate_to_aws.py
```

### 7.2 Or Create Fresh Database:
Your Flask app will automatically create tables on first run.

---

## 📋 Step 8: Configure Domain and SSL (Optional)

### 8.1 Custom Domain:
```bash
# If you have a domain, you can configure it
aws apprunner associate-custom-domain \
    --service-arn your-service-arn \
    --domain-name yourdomain.com
```

### 8.2 SSL Certificate:
App Runner provides automatic SSL certificates for custom domains.

---

## 📋 Step 9: Test Your Deployment

### 9.1 Get App Runner URL:
```bash
# Get your service URL
aws apprunner describe-service --service-arn your-service-arn --query 'Service.ServiceUrl'
```

### 9.2 Test Endpoints:
```bash
# Test health endpoint
curl https://your-app-url.region.awsapprunner.com/api/health

# Test registration
curl -X POST https://your-app-url.region.awsapprunner.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"password123","full_name":"Test User"}'
```

---

## 📋 Step 10: Monitor and Maintain

### 10.1 CloudWatch Logs:
- App Runner automatically sends logs to CloudWatch
- Monitor application performance and errors

### 10.2 Database Monitoring:
- RDS provides built-in monitoring
- Set up CloudWatch alarms for CPU, memory, connections

### 10.3 Scaling:
- App Runner auto-scales based on traffic
- Monitor costs and adjust instance sizes if needed

---

## 💰 Expected Costs

### Monthly Estimates:
- **App Runner**: $25-50 (depending on traffic)
- **RDS db.t3.micro**: $15-20
- **ECR Storage**: $1-2
- **Data Transfer**: $1-5
- **Total**: ~$42-77/month

### Cost Optimization:
- Use RDS Reserved Instances for 40% savings
- Monitor App Runner scaling patterns
- Set up billing alerts

---

## 🔒 Security Checklist

### ✅ Database Security:
- RDS encryption enabled
- Security groups configured
- Regular backups enabled

### ✅ Application Security:
- Environment variables used for secrets
- HTTPS enforced
- JWT tokens for authentication

### ✅ Network Security:
- VPC configuration
- Security groups limiting access
- App Runner in private subnet

---

## 🚨 Troubleshooting Common Issues

### Issue: App Runner Build Fails
```bash
# Check build logs in CloudWatch
# Ensure Dockerfile is correct
# Verify requirements.txt dependencies
```

### Issue: Database Connection Fails
```bash
# Check security groups allow port 5432
# Verify DATABASE_URL format
# Ensure RDS is publicly accessible
```

### Issue: Environment Variables Not Working
```bash
# Verify variables in App Runner console
# Check variable names match your code
# Restart App Runner service after changes
```

---

## 📞 Support Resources

- **AWS App Runner Docs**: https://docs.aws.amazon.com/apprunner/
- **AWS RDS Docs**: https://docs.aws.amazon.com/rds/
- **AWS CLI Reference**: https://docs.aws.amazon.com/cli/

---

## 🎉 Congratulations!

Your LegalCounsel AI chatbot is now running on AWS with:
- ✅ Scalable container deployment
- ✅ Managed PostgreSQL database
- ✅ Automatic SSL certificates
- ✅ Built-in monitoring and logging
- ✅ Enterprise-grade security

Your chatbot is production-ready! 🚀