from rest_framework import serializers
from .models import Feedback, Doubt


class FeedbackSerializer(serializers.ModelSerializer):
    student_username = serializers.SerializerMethodField(read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    content_title = serializers.CharField(source='content.title', read_only=True)

    class Meta:
        model = Feedback
        fields = '__all__'
        read_only_fields = ('student', 'created_at')

    def get_student_username(self, obj):
        return obj.student.username if obj.student else None


class DoubtSerializer(serializers.ModelSerializer):
    student_username = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Doubt
        fields = '__all__'
        read_only_fields = ('student', 'created_at', 'status', 'teacher', 'resolved_at')

    def get_student_username(self, obj):
        return obj.student.username if obj.student else None
