# Student Complaint Portal

A full-stack web application for students to submit and manage complaints about campus facilities.

## Features

- User authentication (login/signup)
- Submit complaints with categories (Hostel, Canteen, Academics, Transport)
- Vote on complaints
- Comment on complaints
- Upload media (images/videos) with complaints
- Admin panel for moderating complaints
- Analytics dashboard with charts
- Responsive design with dark/light mode

## Tech Stack

- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Python Flask
- **Database**: SQLite with SQLAlchemy
- **Charts**: Chart.js

## Setup Instructions

1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the backend server**:
   ```bash
   python app.py
   ```

3. **Open your browser** and go to `http://localhost:5000`

## API Endpoints

- `GET /` - Serve main page
- `POST /api/login` - User login
- `GET /api/complaints` - Get complaints (with optional category and sort filters)
- `POST /api/complaints` - Create new complaint
- `POST /api/complaints/<id>/vote` - Vote on complaint
- `POST /api/complaints/<id>/comment` - Add comment to complaint
- `DELETE /api/complaints/<id>` - Delete complaint (admin)
- `GET /api/analytics` - Get analytics data

## Default Users

- **Admin**: student_id: `SP23cau144`, password: `121205`
- **Demo users**: Any username will auto-create an account

## File Structure

- `app.py` - Flask backend server
- `index.html` - Main complaints page
- `login.html` - Login page
- `admin.html` - Admin moderation panel
- `dashboard.html` - Analytics dashboard
- `script.js` - Frontend JavaScript
- `style.css` - Stylesheets
- `requirements.txt` - Python dependencies
- `complaints.db` - SQLite database (auto-created)

## Development

The backend uses Flask with SQLAlchemy for database operations. CORS is enabled for frontend-backend communication. Media files are stored as base64 in the database for simplicity.

To modify the application:
1. Edit `app.py` for backend changes
2. Edit HTML/JS files for frontend changes
3. Restart the server after backend changes