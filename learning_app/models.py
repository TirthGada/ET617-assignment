from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title


class Content(models.Model):
    CONTENT_TYPES = [
        ('video', 'Video'),
        ('text', 'Text'),
        ('quiz', 'Quiz'),
    ]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='contents')
    title = models.CharField(max_length=200)
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPES)
    text_content = models.TextField(blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    video_duration = models.IntegerField(default=0, help_text="Duration in seconds")
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Quiz(models.Model):
    content = models.OneToOneField(Content, on_delete=models.CASCADE)
    question = models.TextField()
    option_a = models.CharField(max_length=200)
    option_b = models.CharField(max_length=200)
    option_c = models.CharField(max_length=200)
    option_d = models.CharField(max_length=200)
    correct_answer = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')])
    
    def __str__(self):
        return f"Quiz: {self.content.title}"


class UserProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.ForeignKey(Content, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    video_watched_duration = models.IntegerField(default=0, help_text="Duration watched in seconds")
    quiz_score = models.IntegerField(null=True, blank=True)
    
    class Meta:
        unique_together = ['user', 'content']
    
    def __str__(self):
        return f"{self.user.username} - {self.content.title} - {'Completed' if self.completed else 'In Progress'}"


class ClickstreamEvent(models.Model):
    EVENT_TYPES = [
        ('page_view', 'Page View'),
        ('click', 'Click'),
        ('video_play', 'Video Play'),
        ('video_pause', 'Video Pause'),
        ('video_complete', 'Video Complete'),
        ('quiz_attempt', 'Quiz Attempt'),
        ('quiz_submit', 'Quiz Submit'),
        ('text_read', 'Text Read'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('registration', 'Registration'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    event_context = models.CharField(max_length=500, default="Learning Platform")
    component = models.CharField(max_length=100)
    event_name = models.CharField(max_length=50, choices=EVENT_TYPES)
    description = models.TextField()
    origin = models.CharField(max_length=10, default="web")
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    url = models.URLField(max_length=500)
    referrer = models.URLField(max_length=500, blank=True, null=True)
    session_id = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        username = self.user.username if self.user else "Anonymous"
        return f"{username} - {self.event_name} - {self.timestamp}"


class VideoAnalytics(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.ForeignKey(Content, on_delete=models.CASCADE)
    play_timestamp = models.DateTimeField(auto_now_add=True)
    pause_timestamp = models.DateTimeField(null=True, blank=True)
    current_time = models.IntegerField(default=0, help_text="Current playback time in seconds")
    total_watched = models.IntegerField(default=0, help_text="Total time watched in seconds")
    completed = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username} - {self.content.title} - {self.current_time}s" 