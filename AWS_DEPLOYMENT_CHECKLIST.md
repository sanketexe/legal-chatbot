# 🚀 AWS Deployment Checklist for LegalCounsel AI

## ✅ Pre-Deployment Checklist

### Prerequisites:
- [ ] AWS Account with billing configured
- [ ] AWS CLI installed and configured (`aws configure`)
- [ ] Docker Desktop installed and running
- [ ] Gemini API key ready
- [ ] Strong JWT secret key prepared
- [ ] Database password (min 8 characters)

### Verify Tools:
```bash
aws --version          # Should show AWS CLI version
docker --version       # Should show Docker version
aws sts get-caller-identity  # Should show your AWS account info
```

---

## 🗄️ Database Setup (Step 1)

### Option A: Automated Script
```powershell
.\setup_aws_database.ps1
```

### Option B: Manual RDS Creation
```bash
aws rds create-db-instance \
    --db-instance-identifier legal-chatbot-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --master-username legaladmin \
    --master-user-password "YourPassword123!" \
    --allocated-storage 20 \
    --publicly-accessible \
    --storage-encrypted
```

### Database Checklist:
- [ ] RDS instance created and available
- [ ] Database endpoint URL obtained
- [ ] Security group allows port 5432
- [ ] Connection string format: `postgresql://legaladmin:password@endpoint:5432/legalchatbot`

---

## 🐳 Container Setup (Step 2)

### Build and Push to ECR:
```bash
# 1. Create ECR repository
aws ecr create-repository --repository-name legal-chatbot

# 2. Get login token and login
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ACCOUNT-ID.dkr.ecr.us-east-1.amazonaws.com

# 3. Build Docker image
docker build -t legal-chatbot .

# 4. Tag for ECR
docker tag legal-chatbot:latest ACCOUNT-ID.dkr.ecr.us-east-1.amazonaws.com/legal-chatbot:latest

# 5. Push to ECR
docker push ACCOUNT-ID.dkr.ecr.us-east-1.amazonaws.com/legal-chatbot:latest
```

### Container Checklist:
- [ ] ECR repository created
- [ ] Docker image built successfully
- [ ] Image pushed to ECR
- [ ] Image URI copied for App Runner

---

## 🚀 App Runner Deployment (Step 3)

### Via AWS Console:
1. [ ] Go to AWS App Runner Console
2. [ ] Click "Create service"
3. [ ] Choose "Container registry"
4. [ ] Select your ECR image
5. [ ] Configure service settings:
   - **Service name**: `legal-chatbot-service`
   - **CPU**: 0.25 vCPU
   - **Memory**: 0.5 GB
   - **Port**: 8080

### Environment Variables to Add:
```
FLASK_ENV=production
DATABASE_URL=postgresql://legaladmin:password@your-endpoint:5432/legalchatbot
JWT_SECRET_KEY=your-secure-jwt-secret
GEMINI_API_KEY=your-gemini-api-key
```

### App Runner Checklist:
- [ ] Service created successfully
- [ ] Environment variables configured
- [ ] Service is running and healthy
- [ ] App Runner URL obtained

---

## 🧪 Testing (Step 4)

### Test Endpoints:
```bash
# Health check
curl https://your-app-url.awsapprunner.com/api/health

# Register test user
curl -X POST https://your-app-url.awsapprunner.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"password123","full_name":"Test User"}'

# Login test
curl -X POST https://your-app-url.awsapprunner.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}'
```

### Testing Checklist:
- [ ] Health endpoint responds
- [ ] User registration works
- [ ] User login works
- [ ] Chat functionality works
- [ ] Database stores conversations
- [ ] UI loads correctly

---

## 🔧 Post-Deployment (Step 5)

### Monitoring Setup:
- [ ] CloudWatch logs accessible
- [ ] App Runner metrics monitored
- [ ] RDS monitoring configured
- [ ] Billing alerts set up

### Security Review:
- [ ] Environment variables secured
- [ ] Database security groups configured
- [ ] HTTPS enforced (automatic with App Runner)
- [ ] No sensitive data in logs

### Performance Optimization:
- [ ] Monitor response times
- [ ] Check database query performance
- [ ] Verify auto-scaling behavior
- [ ] Review cost optimization opportunities

---

## 💰 Cost Monitoring

### Expected Monthly Costs:
- **App Runner**: $25-50
- **RDS db.t3.micro**: $15-20
- **ECR Storage**: $1-2
- **Data Transfer**: $1-5
- **Total**: ~$42-77/month

### Cost Optimization:
- [ ] Set up AWS Budgets
- [ ] Monitor usage patterns
- [ ] Consider Reserved Instances for RDS
- [ ] Review scaling settings

---

## 🚨 Troubleshooting

### Common Issues:

**App Runner fails to start:**
- Check CloudWatch logs
- Verify environment variables
- Ensure Docker image works locally

**Database connection fails:**
- Verify DATABASE_URL format
- Check security groups
- Ensure RDS is publicly accessible

**Build fails:**
- Check requirements.txt dependencies
- Verify Dockerfile syntax
- Test Docker build locally

### Quick Commands:
```bash
# Check App Runner service status
aws apprunner describe-service --service-arn YOUR-SERVICE-ARN

# View CloudWatch logs
aws logs describe-log-groups --log-group-name-prefix /aws/apprunner

# Check RDS status
aws rds describe-db-instances --db-instance-identifier legal-chatbot-db
```

---

## 🎉 Success Criteria

Your deployment is successful when:
- [ ] App Runner service shows "Running" status
- [ ] Health endpoint returns 200 OK
- [ ] Users can register and login
- [ ] Chat conversations are saved
- [ ] UI is accessible and responsive
- [ ] All functionality works as expected

**Congratulations! Your LegalCounsel AI is live on AWS! 🚀**

---

## 📞 Support Resources

- **AWS App Runner Docs**: https://docs.aws.amazon.com/apprunner/
- **AWS RDS Docs**: https://docs.aws.amazon.com/rds/
- **Docker Docs**: https://docs.docker.com/
- **Flask Deployment**: https://flask.palletsprojects.com/en/2.3.x/deploying/