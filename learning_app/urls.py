from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('content/<int:content_id>/', views.content_view, name='content_view'),
    path('submit-quiz/<int:content_id>/', views.submit_quiz, name='submit_quiz'),
    path('track-video/', views.track_video, name='track_video'),
    path('mark-read/<int:content_id>/', views.mark_content_read, name='mark_content_read'),
    path('admin-analytics/', views.admin_analytics_view, name='admin_analytics'),
    path('admin-login/', views.admin_login_view, name='admin_login'),
] 