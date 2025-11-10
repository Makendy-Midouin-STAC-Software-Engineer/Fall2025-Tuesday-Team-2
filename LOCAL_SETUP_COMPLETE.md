# StudyBuddy Local Setup - Complete ✅

## Server Status
✅ **RUNNING** on `0.0.0.0:8000`

## Access URLs

### Main Application
- **URL:** http://127.0.0.1:8000/
- **Admin Panel:** http://127.0.0.1:8000/admin/

## Login Credentials

### Superuser Account
- **Username:** `Group2Admin`
- **Password:** `Team2Fall2025!`
- **Email:** studybuddy@gmail.com

## Features to Test

### 1. Edit Profile Feature
1. Log in as `Group2Admin`
2. On the home screen, click the **"Edit Profile"** button (green button in the header)
3. Update:
   - Username
   - First Name
   - Last Name
4. Click "Save Changes"
5. Verify:
   - Redirects to home page
   - Success message appears
   - Changes are saved

### 2. Real-Time Chat Feature
1. Create or join a study room
2. Open the room detail page
3. Send a message - it should appear instantly without page reload
4. **Multi-user test:**
   - Open a second browser window/tab
   - Log in as a different user (create one via admin or register)
   - Join the same room
   - Send a message from one client
   - It should appear on the other client within 1.5 seconds (polling interval)

## Admin Panel Access
- Visit: http://127.0.0.1:8000/admin/
- Login with: `Group2Admin` / `Team2Fall2025!`
- Manage users, rooms, messages, etc.

## Server Management

### Stop Server
Press `Ctrl+C` in the terminal where the server is running

### Restart Server
```bash
python manage.py runserver 0.0.0.0:8000
```

### Create Additional Test Users
You can create test users via:
1. Admin panel: http://127.0.0.1:8000/admin/auth/user/add/
2. Registration page: http://127.0.0.1:8000/studybuddy/register/
3. Or run: `python create_superuser.py` (modify script for regular users)

## Notes
- Server is running in the background
- Database is using SQLite (`db.sqlite3`)
- All migrations are applied
- Test coverage: 88.38%
- All 42 tests passing ✅
