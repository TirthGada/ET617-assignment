from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import dashboard_summary, dashboard_chart_data
from . import views

router = DefaultRouter()

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('content/<int:content_id>/', views.content_view, name='content_view'),
    path('submit-quiz/<int:content_id>/', views.submit_quiz_old, name='submit_quiz'),  # Renamed to avoid conflict
    path('track-video/', views.track_video, name='track_video'),
    path('mark-read/<int:content_id>/', views.mark_content_read, name='mark_content_read'),
    path('admin-analytics/', views.admin_analytics_view, name='admin_analytics'),
    path('admin-login/', views.admin_login_view, name='admin_login'),
    
    # ============ NEW QUIZ SYSTEM URLS ============
    
    # Teacher routes
    path('teacher/', views.teacher_login_view, name='teacher_login'),
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/create-quiz/', views.create_quiz, name='create_quiz'),
    path('teacher/quiz/<int:quiz_id>/edit/', views.edit_quiz, name='edit_quiz'),
    path('teacher/quiz/<int:quiz_id>/start/', views.start_quiz, name='start_quiz'),
    path('teacher/quiz/<int:quiz_id>/monitor/', views.quiz_monitor, name='quiz_monitor'),
    path('teacher/quiz/<int:quiz_id>/end/', views.end_quiz, name='end_quiz'),
    path('teacher/quiz/<int:quiz_id>/results/', views.quiz_results, name='quiz_results'),
    path('teacher/quiz/<int:quiz_id>/mistake-analysis/', views.quiz_mistake_analysis, name='quiz_mistake_analysis'),
    
    # Question generation routes
    path('teacher/quiz/<int:quiz_id>/add-manual/', views.add_question_manual, name='add_question_manual'),
    path('teacher/quiz/<int:quiz_id>/generate-text/', views.generate_questions_from_text, name='generate_questions_from_text'),
    path('teacher/quiz/<int:quiz_id>/generate-pdf/', views.generate_questions_from_pdf, name='generate_questions_from_pdf'),
    
    # Student routes
    path('quiz/join/', views.join_quiz, name='join_quiz'),
    path('quiz/<int:quiz_id>/take/', views.take_quiz, name='take_quiz'),
    path('quiz/<int:quiz_id>/submit/', views.submit_quiz, name='submit_quiz_new'),
    path('quiz/<int:quiz_id>/result/', views.quiz_result, name='quiz_result'),
    path('quiz/<int:quiz_id>/help/', views.student_help_content, name='student_help_content'),

    #new
    path('api/', include(router.urls)),
    path('api/dashboard/summary/', dashboard_summary, name='dashboard-summary'),
    path('api/dashboard/chart-data/', dashboard_chart_data, name='dashboard-chart-data'),
] 