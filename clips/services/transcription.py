# clips/services/transcription.py
from faster_whisper import WhisperModel
from django.conf import settings

class TranscriptionService:
    def __init__(self):
        self.model = WhisperModel(
            settings.WHISPER_MODEL_SIZE,
            device=settings.WHISPER_DEVICE,
            compute_type=settings.WHISPER_COMPUTE_TYPE
        )
    
    def transcribe(self, file_path: str) -> list:
        """
        Transcribe audio/video file and return segments with timestamps
        Returns: List of dicts with 'start', 'end', 'text'
        """
        segments, info = self.model.transcribe(
            file_path,
            beam_size=5,
            word_timestamps=True,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )
        
        result = []
        for segment in segments:
            result.append({
                'start': segment.start,
                'end': segment.end,
                'text': segment.text.strip()
            })
        
        return result