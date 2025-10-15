from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
import random
import string


class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title

class Feedback(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1,6)]
    CLARITY_CHOICES = [('easy','Easy'), ('moderate','Moderate'), ('difficult','Difficult')]
    ENGAGEMENT_CHOICES = [('boring','Boring'), ('okay','Okay'), ('engaging','Engaging')]

    student = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    anonymous = models.BooleanField(default=False)
    course = models.ForeignKey('learning_app.Course', on_delete=models.CASCADE)
    content = models.ForeignKey('learning_app.Content', null=True, blank=True, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, null=True, blank=True)
    clarity = models.CharField(max_length=20, choices=CLARITY_CHOICES, null=True, blank=True)
    engagement = models.CharField(max_length=20, choices=ENGAGEMENT_CHOICES, null=True, blank=True)
    instructor_rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, null=True, blank=True)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    metadata = models.JSONField(default=dict, blank=True)  # optional: browser, device, etc.

    class Meta:
        indexes = [
            models.Index(fields=['course', 'created_at']),
            models.Index(fields=['content']),
        ]

class Doubt(models.Model):
    STATUS_CHOICES = [('unanswered','Unanswered'), ('answered','Answered'), ('in_progress','In progress')]

    student = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    anonymous = models.BooleanField(default=False)
    course = models.ForeignKey('learning_app.Course', on_delete=models.CASCADE)
    content = models.ForeignKey('learning_app.Content', null=True, blank=True, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unanswered')
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='handled_doubts', on_delete=models.SET_NULL)
    resolution = models.TextField(blank=True)  # teacher response or link
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['course', 'status']),
            models.Index(fields=['content']),
        ]


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


# New Quiz System Models

class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Teacher: {self.user.username}"


class LiveQuiz(models.Model):
    QUIZ_STATUS = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('ended', 'Ended'),
    ]
    
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    quiz_code = models.CharField(max_length=8, unique=True, blank=True)
    status = models.CharField(max_length=10, choices=QUIZ_STATUS, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    time_limit = models.IntegerField(default=30, help_text="Time limit in minutes")
    
    def save(self, *args, **kwargs):
        if not self.quiz_code:
            self.quiz_code = self.generate_quiz_code()
        super().save(*args, **kwargs)
    
    def generate_quiz_code(self):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    def __str__(self):
        return f"{self.title} ({self.quiz_code})"


class QuizQuestion(models.Model):
    QUESTION_TYPES = [
        ('mcq', 'Multiple Choice'),
        ('true_false', 'True/False'),
    ]
    
    GENERATION_METHOD = [
        ('manual', 'Manual'),
        ('llm_text', 'LLM from Text'),
        ('llm_pdf', 'LLM from PDF'),
    ]
    
    quiz = models.ForeignKey(LiveQuiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=15, choices=QUESTION_TYPES, default='mcq')
    option_a = models.CharField(max_length=500, blank=True)
    option_b = models.CharField(max_length=500, blank=True)
    option_c = models.CharField(max_length=500, blank=True)
    option_d = models.CharField(max_length=500, blank=True)
    correct_answer = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')])
    explanation = models.TextField(blank=True)
    generation_method = models.CharField(max_length=15, choices=GENERATION_METHOD, default='manual')
    source_text = models.TextField(blank=True, help_text="Source text used for LLM generation")
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.quiz.title} - Q{self.order}"


class QuizParticipant(models.Model):
    quiz = models.ForeignKey(LiveQuiz, on_delete=models.CASCADE, related_name='participants')
    student_name = models.CharField(max_length=100)
    student_email = models.EmailField()
    joined_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    score = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['quiz', 'student_email']
    
    def __str__(self):
        return f"{self.student_name} - {self.quiz.title}"


class QuizAnswer(models.Model):
    participant = models.ForeignKey(QuizParticipant, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE)
    selected_answer = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')])
    is_correct = models.BooleanField(default=False)
    answered_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['participant', 'question']
    
    def __str__(self):
        return f"{self.participant.student_name} - {self.question.quiz.title} - Q{self.question.order}"


class StudentAnalysis(models.Model):
    participant = models.OneToOneField(QuizParticipant, on_delete=models.CASCADE, related_name='analysis')
    weak_topics = models.JSONField(default=list, help_text="Topics where student performed poorly")
    strong_topics = models.JSONField(default=list, help_text="Topics where student performed well")
    recommendations = models.TextField(blank=True)
    reading_material = models.TextField(blank=True)
    practice_questions = models.JSONField(default=list, help_text="Additional practice questions")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Analysis for {self.participant.student_name}"


class QuizAnalytics(models.Model):
    quiz = models.OneToOneField(LiveQuiz, on_delete=models.CASCADE, related_name='analytics')
    total_participants = models.IntegerField(default=0)
    average_score = models.FloatField(default=0.0)
    completion_rate = models.FloatField(default=0.0)
    difficult_questions = models.JSONField(default=list, help_text="Questions with low success rate")
    common_mistakes = models.JSONField(default=dict, help_text="Word cloud data for common wrong answers")
    topic_performance = models.JSONField(default=dict, help_text="Performance by topic")
    generated_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Analytics for {self.quiz.title}" 


