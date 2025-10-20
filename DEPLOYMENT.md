# StudyBuddy Deployment Guide

This guide will help you deploy StudyBuddy to production.

**Note:** Email verification is currently disabled for easier deployment. Users can register and login immediately without email verification. The email verification code is still in the codebase and can be re-enabled later if needed.

## 🚀 Quick Deployment Checklist

### Required Environment Variables

**Minimal deployment (current configuration):**

```bash
DEBUG=False
DJANGO_SECRET_KEY=your-randomly-generated-secret-key
```

**Optional - For email features (password reset, etc.):**

```bash
EMAIL_HOST_PASSWORD=your-email-api-key
DEFAULT_FROM_EMAIL=StudyBuddy <noreply@yourdomain.com>
```

---

## 📧 Email Configuration Options

### Option 1: SendGrid (Recommended - Free Tier Available)

1. Sign up at https://sendgrid.com (Free: 100 emails/day)
2. Create an API key
3. Set these environment variables:

```bash
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-api-key
DEFAULT_FROM_EMAIL=StudyBuddy <noreply@yourdomain.com>
```

### Option 2: Gmail

1. Enable 2-Factor Authentication on your Google account
2. Generate an App Password: https://myaccount.google.com/apppasswords
3. Set these environment variables:

```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
DEFAULT_FROM_EMAIL=StudyBuddy <your-email@gmail.com>
```

---

## 🌐 Platform-Specific Instructions

### Heroku Deployment

1. Install Heroku CLI
2. Login and create app:
   ```bash
   heroku login
   heroku create your-app-name
   ```

3. Set environment variables:
   ```bash
   heroku config:set DEBUG=False
   heroku config:set DJANGO_SECRET_KEY="your-secret-key"
   heroku config:set EMAIL_HOST_PASSWORD="your-api-key"
   ```

4. Deploy:
   ```bash
   git push heroku main
   heroku run python manage.py migrate
   ```

### AWS Elastic Beanstalk

1. Install EB CLI
2. Initialize and deploy:
   ```bash
   eb init
   eb create studybuddy-env
   ```

3. Set environment variables in AWS Console or via CLI:
   ```bash
   eb setenv DEBUG=False DJANGO_SECRET_KEY=xxx EMAIL_HOST_PASSWORD=xxx
   ```

### Render.com

1. Create new Web Service
2. Connect your GitHub repo
3. Add environment variables in the dashboard
4. Deploy automatically on push

---

## 🔐 Security Notes

- **Never commit** your `.env` file or environment variables to Git
- **Always use** strong, randomly generated secret keys in production
- **Set DEBUG=False** in production
- **Use HTTPS** for production deployments

---

## ✅ Testing Email in Production

After deployment:

1. Register a new account with your real email
2. Check your inbox for the verification email
3. Click the verification link
4. Login successfully

---

## 📝 Features Included

- ✅ Email verification on registration
- ✅ Password reset via email
- ✅ Pomodoro timer in study rooms
- ✅ Room creation and deletion
- ✅ Message deletion
- ✅ Notes management
- ✅ User authentication

---

## 🆘 Troubleshooting

### Emails not sending?
- Check EMAIL_HOST_PASSWORD is set correctly
- Verify your email service API key is active
- Check spam folder

### Secret key errors?
- Generate a new secret key: `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`
- Set it as DJANGO_SECRET_KEY environment variable

### Database errors?
- Run migrations: `python manage.py migrate`
- In Heroku: `heroku run python manage.py migrate`

---

For questions or issues, please contact the development team.

