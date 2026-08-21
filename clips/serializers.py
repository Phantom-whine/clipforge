# clips/serializers.py
from rest_framework import serializers
from .models import Project, Clip

class ClipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clip
        fields = [
            'id', 'title', 'start_time', 'end_time', 'duration',
            'why_this_clip', 'hook_strength', 'curiosity', 'standalone',
            'value', 'entertainment', 'overall_score', 'clip_file', 'created_at'
        ]

class ProjectSerializer(serializers.ModelSerializer):
    clips = ClipSerializer(many=True, read_only=True)
    
    class Meta:
        model = Project
        fields = [
            'id', 'name', 'description', 'original_file', 'file_type',
            'target_duration', 'clip_count', 'moment_types',
            'status', 'error_message', 'created_at', 'updated_at', 'clips'
        ]
        read_only_fields = ['status', 'error_message', 'created_at', 'updated_at']

class ProjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = [
            'name', 'description', 'original_file', 'file_type',
            'target_duration', 'clip_count', 'moment_types'
        ]
    
    def validate_moment_types(self, value):
        valid_types = [choice[0] for choice in Project.MOMENT_TYPES]
        for moment_type in value:
            if moment_type not in valid_types:
                raise serializers.ValidationError(f"Invalid moment type: {moment_type}")
        return value
    
    def validate_file_type(self, value):
        if value not in ['mp3', 'mp4']:
            raise serializers.ValidationError("File type must be 'mp3' or 'mp4'")
        return value