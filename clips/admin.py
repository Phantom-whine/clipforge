# clips/admin.py
from django.contrib import admin
from .models import Project, Clip

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'file_type', 'target_duration', 'clip_count', 'created_at']
    list_filter = ['status', 'file_type', 'target_duration']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Clip)
class ClipAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'start_time', 'end_time', 'overall_score']
    list_filter = ['project']
    search_fields = ['title']