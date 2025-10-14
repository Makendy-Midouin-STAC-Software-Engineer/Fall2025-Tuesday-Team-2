# Study Buddy - Django Web Application

A collaborative study platform where students can create study rooms and chat with each other in real-time.

## Features

- **User Authentication**: Register, login, and logout functionality
- **Study Rooms**: Create and browse study rooms
- **Real-time Messaging**: Send and receive messages within study rooms
- **Modern UI**: Clean, responsive design with a beautiful interface

## Tech Stack

- **Backend**: Django 5.2.7
- **Database**: SQLite
- **Frontend**: HTML, CSS (inline)
- **Python**: 3.11+

## Setup Instructions

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd Fall2025-Tuesday-Team-2-main
```

### 2. Create Virtual Environment
```bash
python -m venv venv
```

### 3. Activate Virtual Environment
- **Windows**: `venv\Scripts\activate`
- **Mac/Linux**: `source venv/bin/activate`

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Navigate to Project Directory
```bash
cd Fall2025-Tuesday-Team-2-main
```

### 6. Run Migrations
```bash
python manage.py migrate
```

### 7. Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

### 8. Run Development Server
```bash
python manage.py runserver
```

### 9. Access the Application
Open your browser and go to: **http://127.0.0.1:8000/**

## Usage

1. **Register** a new account at `/studybuddy/register/`
2. **Login** with your credentials
3. **Create a study room** by filling out the form on the main page
4. **Click on a room** to enter and start chatting
5. **Send messages** to communicate with other students

## Project Structure

```
Fall2025-Tuesday-Team-2-main/
├── manage.py
├── mysite/              # Main project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── polls/               # Polls app (legacy)
├── studybuddy/          # Study Buddy app
│   ├── models.py        # Room and Message models
│   ├── views.py         # View functions
│   ├── urls.py          # URL routing
│   └── templates/       # HTML templates
├── requirements.txt     # Python dependencies
└── db.sqlite3          # Database (not in git)
```

## Important Notes

- The `db.sqlite3` file is not included in the repository (it's in `.gitignore`)
- After cloning, you'll need to run migrations to create your own database
- The SECRET_KEY in `settings.py` should be changed for production
- DEBUG should be set to `False` in production

## Contributing

This is a class project for Fall 2025 Tuesday Team 2.

## License

Educational use only.