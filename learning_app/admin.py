from django.contrib import admin
from .models import Course, Content, Quiz, UserProgress, ClickstreamEvent, VideoAnalytics, TeacherProfile, LiveQuiz, QuizQuestion, QuizParticipant, QuizAnswer, StudentAnalysis, QuizAnalytics


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_at']
    search_fields = ['title', 'description']
    list_filter = ['created_at']


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'content_type', 'order', 'created_at']
    list_filter = ['content_type', 'course', 'created_at']
    search_fields = ['title', 'course__title']
    ordering = ['course', 'order']


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['content', 'question', 'correct_answer']
    search_fields = ['question', 'content__title']
    list_filter = ['correct_answer']


@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'content', 'completed', 'completed_at', 'quiz_score']
    list_filter = ['completed', 'content__content_type', 'completed_at']
    search_fields = ['user__username', 'content__title']
    raw_id_fields = ['user', 'content']


@admin.register(ClickstreamEvent)
class ClickstreamEventAdmin(admin.ModelAdmin):
    list_display = ['user', 'event_name', 'component', 'timestamp', 'ip_address']
    list_filter = ['event_name', 'component', 'timestamp', 'origin']
    search_fields = ['user__username', 'description', 'ip_address']
    readonly_fields = ['timestamp']
    raw_id_fields = ['user']
    
    def has_add_permission(self, request):
        return False  # Don't allow manual addition of clickstream events


@admin.register(VideoAnalytics)
class VideoAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['user', 'content', 'current_time', 'total_watched', 'completed', 'play_timestamp']
    list_filter = ['completed', 'play_timestamp']
    search_fields = ['user__username', 'content__title']
    raw_id_fields = ['user', 'content']


# ============ NEW QUIZ SYSTEM ADMIN ============

@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'email', 'created_at']
    search_fields = ['user__username', 'email']


@admin.register(LiveQuiz)
class LiveQuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'teacher', 'status', 'quiz_code', 'created_at', 'participants_count']
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'teacher__user__username']
    
    def participants_count(self, obj):
        return obj.participants.count()
    participants_count.short_description = 'Participants'


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ['quiz', 'order', 'question_text_short', 'correct_answer', 'generation_method']
    list_filter = ['generation_method', 'quiz__status']
    search_fields = ['question_text', 'quiz__title']
    ordering = ['quiz', 'order']
    
    def question_text_short(self, obj):
        return obj.question_text[:50] + "..." if len(obj.question_text) > 50 else obj.question_text
    question_text_short.short_description = 'Question'


@admin.register(QuizParticipant)
class QuizParticipantAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'student_email', 'quiz', 'score', 'total_questions', 'submitted_at']
    list_filter = ['submitted_at', 'quiz__status']
    search_fields = ['student_name', 'student_email', 'quiz__title']


@admin.register(QuizAnswer)
class QuizAnswerAdmin(admin.ModelAdmin):
    list_display = ['participant', 'question', 'selected_answer', 'is_correct', 'answered_at']
    list_filter = ['is_correct', 'answered_at']
    search_fields = ['participant__student_name', 'question__question_text']


@admin.register(StudentAnalysis)
class StudentAnalysisAdmin(admin.ModelAdmin):
    list_display = ['participant', 'created_at', 'weak_topics_count', 'strong_topics_count']
    search_fields = ['participant__student_name', 'participant__student_email']
    
    def weak_topics_count(self, obj):
        return len(obj.weak_topics)
    weak_topics_count.short_description = 'Weak Topics'
    
    def strong_topics_count(self, obj):
        return len(obj.strong_topics)
    strong_topics_count.short_description = 'Strong Topics'


@admin.register(QuizAnalytics)
class QuizAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['quiz', 'total_participants', 'average_score', 'completion_rate', 'generated_at']
    search_fields = ['quiz__title'] 