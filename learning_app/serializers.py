from rest_framework import serializers
from .models import Feedback, Doubt

class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = '__all__'
        read_only_fields = ('student', 'created_at')


class DoubtSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doubt
        fields = '__all__'
        read_only_fields = ('student', 'created_at', 'status', 'teacher', 'resolved_at')
