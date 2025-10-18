# StudyBuddy - Fall2025-Tuesday-Team-2

A collaborative study platform built with Django featuring study rooms, note-taking, Pomodoro timers, and email authentication.

## 🎯 Features

- **User Authentication**
  - Email verification on registration
  - Password reset via email
  - Secure login/logout

- **Study Rooms**
  - Create and join study rooms
  - Real-time chat messaging
  - Pomodoro timer integration (25-min work / 5-min break)
  - Room deletion for creators
  - Message deletion

- **Notes Management**
  - Create, edit, and delete personal notes
  - Organized note list view

## 🚀 Quick Start (Local Development)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Fall2025-Tuesday-Team-2-main
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run migrations**
   ```bash
   python manage.py migrate
   ```

4. **Start the development server**
   ```bash
   python manage.py runserver
   ```

5. **Access the application**
   - Open http://localhost:8000/studybuddy/
   - Register a new account
   - Verification emails will appear in the terminal

## 📧 Production Deployment

For production deployment with real email sending, see [DEPLOYMENT.md](DEPLOYMENT.md)

**Required Environment Variables:**
- `DEBUG=False`
- `DJANGO_SECRET_KEY=your-secret-key`
- `EMAIL_HOST_PASSWORD=your-email-api-key`

## 🛠️ Tech Stack

- **Backend**: Django 5.2.7
- **Database**: SQLite (development) / PostgreSQL (production ready)
- **Authentication**: Django built-in with custom email verification
- **Email**: Console backend (dev) / SMTP (production)
- **Frontend**: HTML, CSS, JavaScript

## 📁 Project Structure

```
├── mysite/              # Django project settings
├── studybuddy/          # Main application
│   ├── models.py       # Database models
│   ├── views.py        # View logic
│   ├── urls.py         # URL routing
│   └── templates/      # HTML templates
├── polls/              # Polls app (legacy)
├── manage.py           # Django management script
└── requirements.txt    # Python dependencies
```

## 👥 Contributors

Fall 2025 Tuesday Team 2

## 📝 License

This project is for educational purposes.