# clips/tasks.py
from .models import Project, Clip
from .services.transcription import TranscriptionService
from .services.chunking import ChunkingService
from .services.gemini import GeminiService
from .services.ffmpeg import FFmpegService
from django.conf import settings
import os
from pathlib import Path

def process_project(project_id: str):
    """
    Process a project: transcribe, analyze, and extract clips
    This runs synchronously (no Celery)
    """
    try:
        project = Project.objects.get(id=project_id)
        
        # Step 1: Transcribe
        project.status = 'transcribing'
        project.save()
        
        transcription_service = TranscriptionService()
        segments = transcription_service.transcribe(project.original_file.path)
        
        # Step 2: Chunk with padding
        chunking_service = ChunkingService()
        chunks = chunking_service.create_chunks(segments, chunk=False)
        
        # Step 3: Analyze with Gemini
        project.status = 'analyzing'
        project.save()
        
        gemini_service = GeminiService()
        project_settings = {
            'target_duration': project.target_duration,
            'clip_count': project.clip_count,
            'moment_types': project.moment_types,
            'description': project.description,
        }
        
        clip_recommendations = gemini_service.analyze_chunks(chunks, project_settings)
        
        # Step 4: Extract clips
        project.status = 'extracting'
        project.save()
        
        ffmpeg_service = FFmpegService()
        
        # Create output directory
        output_dir = Path(settings.MEDIA_ROOT) / 'uploads' / 'clips' / str(project.id)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for idx, rec in enumerate(clip_recommendations):
            # Generate output filename
            safe_title = "".join(c for c in rec['title'] if c.isalnum() or c in (' ', '-', '_')).strip()
            output_filename = f"clip_{idx+1}_{safe_title[:50]}.mp4"
            output_path = output_dir / output_filename
            
            # Extract clip
            success = ffmpeg_service.extract_clip(
                project.original_file.path,
                str(output_path),
                rec['start_time'],
                rec['end_time']
            )
            
            if success:
                # Create Clip object
                Clip.objects.create(
                    project=project,
                    title=rec['title'],
                    start_time=rec['start_time'],
                    end_time=rec['end_time'],
                    duration=rec['end_time'] - rec['start_time'],
                    why_this_clip=rec['why_this_clip'],
                    hook_strength=rec['hook_strength'],
                    curiosity=rec['curiosity'],
                    standalone=rec['standalone'],
                    value=rec['value'],
                    entertainment=rec['entertainment'],
                    overall_score=rec['overall_score'],
                    clip_file=f'uploads/clips/{project.id}/{output_filename}'
                )
        
        # Mark as completed
        project.status = 'completed'
        project.save()
        
    except Exception as e:
        # Mark as failed
        project.status = 'failed'
        project.error_message = str(e)
        project.save()
        raise