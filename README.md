# Learning Platform - ET617 Assignment

An interactive learning platform built with Django that provides video content, quizzes, and comprehensive analytics tracking.

## 🚀 Features

- **Interactive Video Learning**: Watch educational videos with automatic progress tracking
- **Knowledge Quizzes**: Test understanding with interactive quizzes and instant feedback
- **User Progress Tracking**: Complete activity monitoring and learning insights
- **Admin Analytics Dashboard**: Comprehensive system analytics and user behavior tracking
- **Demo Mode**: No registration required - instant access with any username

## 📋 Quick Start

### Demo Access
- **Login**: Use any username (no password required)
- **Features**: Access to all courses, videos, and quizzes
- **Sample Content**: Pre-loaded courses in Web Development, Data Science, and Digital Marketing

### Admin Analytics Access
- **URL**: Click "Admin Analytics" in the navigation bar
- **Username**: `root`
- **Password**: `root`
- **Features**: 
  - Complete user activity tracking
  - System statistics and metrics
  - Clickstream event monitoring
  - Data export functionality

## 🛠️ Installation & Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ET617-assignment
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup database**
   ```bash
   python manage.py migrate
   ```

4. **Create sample data** (optional)
   ```bash
   python manage.py create_sample_data
   ```

5. **Run the development server**
   ```bash
   python manage.py runserver
   ```

6. **Access the platform**
   - Main Platform: http://localhost:8000/
   - Admin Analytics: http://localhost:8000/admin-login/

## 📁 Project Structure

```
ET617-assignment/
├── learning_app/           # Main Django application
│   ├── models.py          # Database models (User, Course, Content, etc.)
│   ├── views.py           # View functions and business logic
│   ├── urls.py            # URL routing
│   └── management/        # Custom Django commands
├── templates/             # HTML templates
│   └── learning_app/      # App-specific templates
├── static/               # CSS, JS, and static assets
├── requirements.txt      # Python dependencies
└── manage.py            # Django management script
```

## 🎯 Key Components

### User Features
- **Dashboard**: Personal learning progress overview
- **Video Player**: Interactive video content with tracking
- **Quiz System**: Multiple-choice questions with instant feedback
- **Progress Tracking**: Automatic completion status updates

### Admin Analytics
- **User Statistics**: Total users, active sessions, completion rates
- **Content Analytics**: Most viewed videos, quiz performance
- **Clickstream Events**: Detailed user interaction tracking
- **Export Functionality**: Download analytics data as CSV

### Data Models
- **User**: Authentication and user management
- **Course**: Learning course organization
- **Content**: Videos, quizzes, and reading materials
- **UserProgress**: Individual learning progress tracking
- **ClickstreamEvent**: Detailed user activity logging

## 🔐 Authentication & Security

### Demo Mode
- **Login**: Any username works (password optional)
- **Purpose**: Easy demonstration and testing
- **Scope**: Access to all learning content

### Admin Access
- **Credentials**: username=`root`, password=`root`
- **Session-based**: Admin authentication stored in session
- **Protected Routes**: Analytics pages require admin authentication

## 📊 Analytics & Tracking

The platform automatically tracks:
- **Page Views**: Every page visit and navigation
- **Video Interactions**: Play, pause, completion events
- **Quiz Activities**: Attempts, answers, and scores
- **Content Progress**: Reading completion and time spent
- **User Registration**: New account creation

### Analytics Dashboard Features
- Real-time activity monitoring
- User engagement metrics
- Content performance statistics
- System usage analytics
- Data export capabilities

## 🎨 UI/UX Features

- **Responsive Design**: Works on desktop and mobile devices
- **Bootstrap Integration**: Modern, clean interface
- **Font Awesome Icons**: Consistent iconography
- **Progress Indicators**: Visual feedback for learning progress
- **Interactive Elements**: Engaging user experience

## 🚀 Deployment

### Local Development
```bash
python manage.py runserver
```

### Production (using render.yaml)
The project includes render.yaml for easy deployment to Render.com:
- Automatic dependency installation
- Database migrations
- Static file collection

## 📈 Sample Data

The platform includes sample content:
- **3 Courses**: Web Development, Data Science, Digital Marketing
- **Video Content**: Educational videos with metadata
- **Quiz Questions**: Multiple-choice assessments
- **Progress Data**: Example user interactions

## 🛠️ Development Notes

### Key Technologies
- **Backend**: Django 4.x
- **Frontend**: HTML5, Bootstrap 5, JavaScript
- **Database**: SQLite (development), PostgreSQL (production)
- **Icons**: Font Awesome
- **Styling**: Bootstrap + Custom CSS

### Custom Management Commands
- `create_sample_data`: Populates database with demo content
- Automatic clickstream event logging
- Session-based admin authentication

## 📝 API Endpoints

### Public Routes
- `/` - Home page
- `/login/` - User login
- `/dashboard/` - User dashboard (requires login)

### Admin Routes
- `/admin-login/` - Admin authentication
- `/admin-analytics/` - Analytics dashboard (requires admin auth)

### Content Routes
- `/course/<id>/` - Course detail view
- `/content/<id>/` - Content viewing (videos/quizzes)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is created for educational purposes as part of the ET617 assignment.

---

**Note**: This is a demonstration platform designed for educational purposes. In a production environment, implement proper authentication, security measures, and data protection protocols.
