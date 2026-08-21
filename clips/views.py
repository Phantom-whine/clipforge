# clips/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.files.storage import default_storage
from .models import Project, Clip
from .serializers import ProjectSerializer, ProjectCreateSerializer, ClipSerializer
from .tasks import process_project
import threading

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ProjectCreateSerializer
        return ProjectSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        project = serializer.save()
        
        # Process project in background thread
        thread = threading.Thread(target=process_project, args=(str(project.id),))
        thread.start()
        
        return Response(
            ProjectSerializer(project).data,
            status=status.HTTP_201_CREATED
        )

    def perform_destroy(self, instance):
        file_names = [instance.original_file.name]
        file_names.extend(
            clip.clip_file.name
            for clip in instance.clips.all()
            if clip.clip_file
        )
        instance.delete()
        for file_name in file_names:
            if file_name:
                default_storage.delete(file_name)
    
    @action(detail=True, methods=['get'])
    def clips(self, request, pk=None):
        project = self.get_object()
        clips = project.clips.all()
        serializer = ClipSerializer(clips, many=True)
        return Response(serializer.data)


class ClipViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ClipSerializer
    
    def get_queryset(self):
        project_id = self.kwargs.get('project_id')
        return Clip.objects.filter(project_id=project_id)