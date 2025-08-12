from django.contrib import admin
from .models import Course, Content, Quiz, UserProgress, ClickstreamEvent, VideoAnalytics


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