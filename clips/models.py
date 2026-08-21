# clips/models.py
from django.db import models
import uuid

class Project(models.Model):
    DURATION_CHOICES = [
        ('15-30', '15-30 seconds'),
        ('30-60', '30-60 seconds'),
        ('60-90', '60-90 seconds'),
    ]
    
    CLIP_COUNT_CHOICES = [
        ('5', '5 clips'),
        ('8', '8 clips'),
        ('12', '12 clips'),
        ('balanced', 'Balanced'),
    ]
    
    MOMENT_TYPES = [
        ('strong_hooks', 'Strong Hooks'),
        ('surprising_info', 'Surprising Information'),
        ('stories', 'Stories'),
        ('educational', 'Educational Moments'),
        ('emotional', 'Emotional Moments'),
        ('humor', 'Humor'),
        ('controversial', 'Controversial Opinions'),
        ('practical', 'Practical Advice'),
        ('interesting_facts', 'Interesting Facts'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('transcribing', 'Transcribing'),
        ('analyzing', 'Analyzing'),
        ('extracting', 'Extracting Clips'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    original_file = models.FileField(upload_to='uploads/originals/')
    file_type = models.CharField(max_length=10, choices=[('mp3', 'MP3'), ('mp4', 'MP4')])
    description = models.TextField(blank=True, default='')
    
    # Settings
    target_duration = models.CharField(max_length=10, choices=DURATION_CHOICES, default='30-60')
    clip_count = models.CharField(max_length=10, choices=CLIP_COUNT_CHOICES, default='balanced')
    moment_types = models.JSONField(default=list)  # List of moment type strings
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.status}"


class Clip(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='clips')
    
    # Clip metadata
    title = models.CharField(max_length=500)
    start_time = models.FloatField()  # in seconds
    end_time = models.FloatField()  # in seconds
    duration = models.FloatField()  # calculated duration
    
    # AI analysis
    why_this_clip = models.TextField()
    hook_strength = models.IntegerField()  # 0-100
    curiosity = models.IntegerField()  # 0-100
    standalone = models.IntegerField()  # 0-100
    value = models.IntegerField()  # 0-100
    entertainment = models.IntegerField()  # 0-100
    overall_score = models.IntegerField()  # 0-100
    
    # Files
    clip_file = models.FileField(upload_to='uploads/clips/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['start_time']
    
    def __str__(self):
        return f"{self.title} ({self.start_time:.2f}s - {self.end_time:.2f}s)"