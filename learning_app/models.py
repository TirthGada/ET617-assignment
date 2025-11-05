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
        ('subjective', 'Subjective'),
    ]
    
    GENERATION_METHOD = [
        ('manual', 'Manual'),
        ('llm_text', 'LLM from Text'),
        ('llm_pdf', 'LLM from PDF'),
    ]
    
    APPROVAL_STATUS = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    quiz = models.ForeignKey(LiveQuiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=15, choices=QUESTION_TYPES, default='mcq')
    option_a = models.CharField(max_length=500, blank=True)
    option_b = models.CharField(max_length=500, blank=True)
    option_c = models.CharField(max_length=500, blank=True)
    option_d = models.CharField(max_length=500, blank=True)
    correct_answer = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')], blank=True)
    explanation = models.TextField(blank=True)
    generation_method = models.CharField(max_length=15, choices=GENERATION_METHOD, default='manual')
    source_text = models.TextField(blank=True, help_text="Source text used for LLM generation")
    order = models.PositiveIntegerField(default=0)
    
    # New approval field
    approval_status = models.CharField(max_length=15, choices=APPROVAL_STATUS, default='approved')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.quiz.title} - Q{self.order}"
    
    def save(self, *args, **kwargs):
        # Auto-approve manual questions, set LLM questions to pending
        if not self.pk:  # New question
            if self.generation_method == 'manual':
                self.approval_status = 'approved'
            else:
                self.approval_status = 'pending'
        super().save(*args, **kwargs)



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


class SubjectiveAnswer(models.Model):
    participant = models.ForeignKey(QuizParticipant, on_delete=models.CASCADE, related_name='subjective_answers')
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE)
    answer_text = models.TextField()
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['participant', 'question']

    def __str__(self):
        return f"{self.participant.student_name} - Subjective - Q{self.question.order}"


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


# ============ POLL SYSTEM MODELS ============

class Poll(models.Model):
    POLL_TYPES = [
        ('single_choice', 'Single Choice'),
        ('multiple_choice', 'Multiple Choice'),
        ('text_response', 'Text Response'),
        ('rating_scale', 'Rating Scale (1-5)'),
        ('yes_no', 'Yes/No'),
    ]
    
    POLL_STATUS = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('ended', 'Ended'),
    ]
    
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    poll_type = models.CharField(max_length=20, choices=POLL_TYPES, default='single_choice')
    poll_code = models.CharField(max_length=8, unique=True, blank=True)
    status = models.CharField(max_length=10, choices=POLL_STATUS, default='draft')
    is_anonymous = models.BooleanField(default=False, help_text="If True, responses are anonymous")
    allow_multiple_responses = models.BooleanField(default=False, help_text="Allow same person to respond multiple times")
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.poll_code:
            self.poll_code = self.generate_poll_code()
        super().save(*args, **kwargs)
    
    def generate_poll_code(self):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    def __str__(self):
        return f"{self.title} ({self.poll_code})"


class PollOption(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='options')
    option_text = models.CharField(max_length=500)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.poll.title} - Option {self.order}: {self.option_text}"


class PollResponse(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='responses')
    student_name = models.CharField(max_length=100, blank=True, null=True)
    student_email = models.EmailField(blank=True, null=True)
    selected_options = models.JSONField(default=list, help_text="List of selected option IDs for choice polls")
    text_response = models.TextField(blank=True, help_text="Text response for text polls")
    rating_value = models.IntegerField(null=True, blank=True, help_text="Rating value (1-5) for rating polls")
    submitted_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    
    class Meta:
        # Remove the unique constraint to allow multiple responses from same IP when allowed
        # Index on poll and ip_address for performance
        indexes = [
            models.Index(fields=['poll', 'ip_address']),
        ]
    
    def __str__(self):
        if self.student_name:
            return f"{self.student_name} - {self.poll.title}"
        else:
            return f"Anonymous - {self.poll.title}"


class PollAnalytics(models.Model):
    poll = models.OneToOneField(Poll, on_delete=models.CASCADE, related_name='analytics')
    total_responses = models.IntegerField(default=0)
    response_distribution = models.JSONField(default=dict, help_text="Distribution of responses by option")
    average_rating = models.FloatField(default=0.0, help_text="Average rating for rating polls")
    response_timeline = models.JSONField(default=list, help_text="Response timeline data")
    word_cloud_data = models.JSONField(default=dict, help_text="Word frequencies for text response polls")
    word_cloud_generated_at = models.DateTimeField(null=True, blank=True, help_text="When word cloud was last generated")
    generated_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Analytics for {self.poll.title}" 