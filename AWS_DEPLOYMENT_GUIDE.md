# AWS Elastic Beanstalk Deployment Guide

## Prerequisites

Before deploying, make sure you have:

1. **AWS Account** - Sign up at https://aws.amazon.com (Free tier available)
2. **AWS CLI** - Install from https://aws.amazon.com/cli/
3. **EB CLI** - Install using pip: `pip install awsebcli`

---

## Step-by-Step Deployment

### 1. Install AWS CLI (if not installed)

**Windows:**
```powershell
msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi
```

**Verify installation:**
```bash
aws --version
```

### 2. Install EB CLI

```bash
pip install awsebcli
```

**Verify:**
```bash
eb --version
```

### 3. Configure AWS Credentials

```bash
aws configure
```

You'll need:
- AWS Access Key ID (get from AWS Console → IAM → Users → Security Credentials)
- AWS Secret Access Key
- Default region: `us-east-1` (or your preferred region)
- Default output format: `json`

### 4. Initialize Elastic Beanstalk

```bash
eb init
```

Follow the prompts:
- Select region (e.g., us-east-1)
- Application name: `studybuddy`
- Platform: Python
- Platform version: Python 3.11 (or latest)
- SSH: Yes (for debugging)

### 5. Create Environment and Deploy

```bash
eb create studybuddy-env
```

This will:
- Create an environment
- Deploy your application
- Set up load balancer
- Configure security groups
- Run migrations automatically

Wait 5-10 minutes for deployment to complete.

### 6. Set Environment Variables

```bash
eb setenv DEBUG=False
eb setenv DJANGO_SECRET_KEY="your-random-secret-key-here"
eb setenv EMAIL_HOST_PASSWORD="your-sendgrid-api-key"
eb setenv DEFAULT_FROM_EMAIL="StudyBuddy <noreply@yourdomain.com>"
```

### 7. Open Your Application

```bash
eb open
```

This opens your app in the browser!

---

## Get Email Working (SendGrid)

1. Sign up at https://sendgrid.com (free tier: 100 emails/day)
2. Create API key
3. Set environment variable:

```bash
eb setenv EMAIL_HOST=smtp.sendgrid.net
eb setenv EMAIL_PORT=587
eb setenv EMAIL_USE_TLS=True
eb setenv EMAIL_HOST_USER=apikey
eb setenv EMAIL_HOST_PASSWORD=your-sendgrid-api-key-here
```

---

## Useful Commands

```bash
# Check status
eb status

# View logs
eb logs

# SSH into instance
eb ssh

# Deploy updates
git add .
git commit -m "Update"
eb deploy

# Terminate environment (cleanup)
eb terminate studybuddy-env
```

---

## Troubleshooting

### Issue: Deployment Failed
```bash
eb logs
```
Check the logs for errors.

### Issue: Static Files Not Loading
```bash
eb ssh
cd /var/app/current
source /var/app/venv/*/bin/activate
python manage.py collectstatic --noinput
```

### Issue: Database Errors
Migrations run automatically on deployment. If issues occur:
```bash
eb ssh
cd /var/app/current
source /var/app/venv/*/bin/activate
python manage.py migrate
```

---

## Cost

- **Free Tier**: First 750 hours/month free for 12 months
- **After free tier**: ~$20-30/month for small app

To avoid charges, terminate when not in use:
```bash
eb terminate studybuddy-env
```

---

## Production Checklist

- [ ] Set DEBUG=False
- [ ] Configure SendGrid for emails
- [ ] Set strong SECRET_KEY
- [ ] Review security settings
- [ ] Set up custom domain (optional)
- [ ] Enable HTTPS (automatic with EB)

---

Your app will be live at: `http://studybuddy-env.eba-xxxxx.us-east-1.elasticbeanstalk.com`

