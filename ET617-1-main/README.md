# ET617 Learning Platform

An intelligent educational platform that combines traditional e-learning features with AI-powered quiz generation and comprehensive analytics tracking.

## 🚀 Quick Start

### Setup
```bash
# Navigate to project directory
cd ET617-assignment-main

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
python manage.py migrate

# Create sample data (optional)
python manage.py create_sample_data

# Start development server
python manage.py runserver
```

### Access the Application
- **Main Application**: http://127.0.0.1:8000/
- **Admin Analytics**: http://127.0.0.1:8000/admin-analytics/ (username: `root`, password: `root`)

## 👨‍🎓 Student Features

### **Account & Access**
- **Easy Login**: Use any username (no password required for demo)
- **Instant Access**: No registration needed - just enter a username
- **Progress Tracking**: Automatic tracking of learning progress

### **Learning Content**
- **Interactive Videos**: Watch educational videos with automatic progress tracking
- **Text Content**: Read articles and mark them as completed
- **Course Navigation**: Browse through different courses and topics
- **Progress Monitoring**: See completion percentage and learning statistics

### **Quiz System**
- **Join Live Quizzes**: Enter quiz codes to participate in real-time quizzes
- **Multiple Choice Questions**: Answer questions with immediate feedback
- **Instant Results**: Get immediate scores and correct answers
- **Quiz History**: View your quiz attempts and performance

### **Poll System**
- **Join Polls**: Enter poll codes to participate in real-time polls and surveys
- **Multiple Poll Types**: Single choice, multiple choice, text responses, rating scales, yes/no
- **Anonymous Participation**: Option to participate anonymously or with identification
- **Instant Feedback**: See poll results and response confirmation
- **QR Code Access**: Scan QR codes for quick poll access
- **Mobile-Friendly**: Responsive design for easy mobile participation

### **Personalized Learning**
- **AI-Generated Analysis**: Receive personalized learning recommendations
- **Weak Topic Identification**: Get insights on areas needing improvement
- **Study Recommendations**: AI-powered suggestions for better learning
- **Practice Questions**: Additional questions based on your performance

### **Help & Support**
- **AI-Powered Help**: Get personalized help content when struggling
- **Mistake Analysis**: Understand why answers were wrong
- **Learning Resources**: Access additional study materials
- **Progress Insights**: Track your learning journey

## 👨‍🏫 Teacher Features

### **Account Management**
- **Teacher Registration**: Create teacher accounts with email
- **Secure Login**: Dedicated teacher authentication system
- **Profile Management**: Manage teacher profile and settings

### **Quiz Creation**
- **Live Quiz System**: Create real-time quizzes with unique codes
- **Multiple Question Types**: Create multiple choice and true/false questions
- **Time Limits**: Set custom time limits for quizzes
- **Quiz Status Management**: Draft, Active, and Ended quiz states

### **AI-Powered Question Generation**
- **Manual Questions**: Create questions manually with full control
- **Text-to-Questions**: Generate questions from any text content
- **PDF-to-Questions**: Upload PDF files and generate questions automatically
- **Smart Question Parsing**: AI automatically formats questions correctly
- **Multiple AI APIs**: Uses Groq, Hugging Face, and other AI services
- **Fallback System**: Always generates questions even if AI fails

### **Question Management**
- **Question Ordering**: Arrange questions in desired sequence
- **Question Editing**: Modify existing questions easily
- **Bulk Generation**: Generate multiple questions at once
- **Question Metadata**: Track how questions were generated (manual/AI)

### **Live Quiz Management**
- **Quiz Monitoring**: Monitor active quizzes in real-time
- **Participant Tracking**: See who joined and their progress
- **Quiz Codes**: Generate unique 6-character codes for quiz access
- **Start/Stop Control**: Start and end quizzes as needed

### **Advanced Analytics**
- **Student Performance Analysis**: Detailed insights on student performance
- **Mistake Analysis**: AI-powered analysis of common student mistakes
- **Question Difficulty Analysis**: Identify difficult questions
- **Completion Rates**: Track quiz completion statistics
- **Word Cloud Generation**: Visual representation of common mistakes

### **AI-Powered Insights**
- **Bloom's Taxonomy Questions**: Generate questions at different cognitive levels
- **Personalized Student Analysis**: Individual student performance insights
- **Remedial Content Generation**: Create help content for struggling students
- **Teaching Recommendations**: AI suggestions for improving instruction
- **Topic Performance**: Analyze performance by subject areas

### **Poll Management**
- **Create Polls**: Design interactive polls and surveys for student engagement
- **Multiple Poll Types**: Single choice, multiple choice, text responses, rating scales (1-5), yes/no
- **Real-time Monitoring**: Live dashboard to monitor poll responses and analytics
- **QR Code Generation**: Generate QR codes for easy poll sharing
- **Poll Status Control**: Draft, Active, and Ended poll states with full control
- **Anonymous Options**: Choose between anonymous or identified responses
- **Multiple Response Control**: Allow or prevent multiple responses per student
- **Live Analytics**: Real-time charts and response tracking
- **Poll Codes**: Generate unique 6-character codes for poll access
- **Response Management**: View and analyze all poll responses
- **Export Results**: Access comprehensive poll analytics and data

### **Content Management**
- **Course Creation**: Create and manage educational courses
- **Content Organization**: Organize videos, text, and quizzes
- **Media Upload**: Upload PDF files for question generation
- **Content Tracking**: Monitor student engagement with content

## 🔧 Technical Features

### **AI Integration**
- **Multiple LLM APIs**: Groq, Hugging Face, OpenAI-compatible
- **Intelligent Fallbacks**: Always generates questions even if AI fails
- **Context-Aware Generation**: Questions based on actual content
- **Smart Parsing**: Automatically formats AI responses

### **Analytics & Tracking**
- **Comprehensive Clickstream**: Track all user interactions
- **Video Analytics**: Monitor video watching behavior
- **Quiz Analytics**: Detailed quiz performance metrics
- **User Behavior**: Complete user journey tracking

### **System Features**
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Real-time Updates**: Live quiz and poll monitoring with instant updates
- **QR Code Integration**: Generate and scan QR codes for easy access
- **Chart.js Integration**: Beautiful data visualization for analytics
- **Error Handling**: Graceful error handling and user feedback
- **Performance Optimized**: Fast loading and smooth interactions

## 🎯 Demo Access

### **Students**
- Visit: http://127.0.0.1:8000/
- Enter any username (no password needed)
- Start exploring courses, taking quizzes, and participating in polls
- Use "Join Poll" to participate in real-time polls and surveys

### **Teachers**
- Visit: http://127.0.0.1:8000/teacher/
- Register with your email address
- Create quizzes and generate AI-powered questions
- Create and manage interactive polls and surveys
- Access real-time analytics and monitoring dashboards

### **Admin Analytics**
- Visit: http://127.0.0.1:8000/admin-analytics/
- Username: `root`
- Password: `root`
- View comprehensive system analytics

## 📚 Sample Content

The platform includes sample courses with:
- **Web Development**: HTML, CSS, JavaScript basics
- **Data Science**: Python, statistics, machine learning
- **Digital Marketing**: SEO, social media, analytics

## 🛠️ Technology Stack

- **Backend**: Django 4.2.7
- **Database**: SQLite (development), In-memory (production)
- **Frontend**: Bootstrap 5, HTML5, JavaScript
- **AI Services**: Groq API, Hugging Face Transformers
- **PDF Processing**: PyPDF2
- **QR Code Generation**: qrcode library with Pillow
- **Data Visualization**: Chart.js for interactive charts
- **Analytics**: Custom clickstream tracking
- **Deployment**: Vercel-ready

## 🚀 Getting Started

1. **Clone the repository**
2. **Follow the setup instructions above**
3. **Start the development server**
4. **Visit the application in your browser**
5. **Start exploring as a student or teacher!**

## ✅ Recently Implemented

### **Poll System** ✨ NEW!
- **Complete Poll Management**: Teachers can create, edit, start, monitor, and end polls
- **Multiple Poll Types**: Single choice, multiple choice, text responses, rating scales (1-5), yes/no
- **Real-time Monitoring**: Live dashboard with charts and analytics
- **QR Code Integration**: Generate QR codes for easy poll sharing
- **Student Participation**: Easy poll joining with codes or QR scanning
- **Anonymous Options**: Support for both anonymous and identified responses
- **Mobile Responsive**: Works perfectly on all devices

## 🚧 Work in Progress

### **Enhanced PDF Processing**
- **Increase PDF processing size to 20 pages**: Currently limited to 5 pages, expanding to handle larger educational materials
- **Implement RAG using vector database**: Advanced retrieval-augmented generation for better question quality from large document collections

### **Communication & Support**
- **Doubt asking and answering forum**: Student-teacher interaction platform for questions, discussions, and collaborative learning

## 📝 Notes

- This is a demo/educational platform
- All data is stored locally (SQLite)
- AI features require internet connection
- Perfect for educational technology demonstrations
