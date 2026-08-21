import subprocess
import os
import json
from pathlib import Path

class FFmpegService:
    def extract_clip(self, input_file: str, output_file: str, 
                    start_time: float, end_time: float) -> bool:
        """
        Extract a clip from video/audio using FFmpeg with re-encoding
        for precise cuts at exact timestamps
        Returns True if successful, False otherwise
        """
        try:
            # Validate inputs
            if not os.path.exists(input_file):
                print(f"Input file not found: {input_file}")
                return False
            
            duration = end_time - start_time
            
            if duration <= 0:
                print(f"Invalid duration: {duration}s (start: {start_time}, end: {end_time})")
                return False
            
            # Ensure output directory exists
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Build FFmpeg command with re-encoding for precise cuts
            cmd = [
                'ffmpeg',
                '-ss', str(start_time),      # Start time
                '-i', input_file,             # Input file
                '-t', str(duration),          # Duration of clip
                '-c:v', 'libx264',           # Re-encode video with H.264
                '-preset', 'fast',            # Fast encoding preset
                '-crf', '23',                 # Quality setting (18-28, lower=better)
                '-c:a', 'aac',               # Re-encode audio with AAC
                '-b:a', '128k',              # Audio bitrate
                '-movflags', '+faststart',   # Optimize for web streaming
                '-y',                         # Overwrite output
                output_file                   # Output file path
            ]
            
            # Run FFmpeg
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                timeout=300  # 5 minute timeout
            )
            
            # Verify output file was created
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                return True
            else:
                print(f"Output file not created or empty: {output_file}")
                return False
            
        except subprocess.TimeoutExpired:
            print(f"FFmpeg processing timed out for {input_file}")
            return False
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode() if e.stderr else "Unknown error"
            print(f"FFmpeg error: {error_msg}")
            return False
        except Exception as e:
            print(f"Error extracting clip: {str(e)}")
            return False
    
    def get_media_info(self, file_path: str) -> dict:
        """Get media file information"""
        try:
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                return {}
            
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                file_path
            ]
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                timeout=30
            )
            
            return json.loads(result.stdout.decode())
            
        except subprocess.TimeoutExpired:
            print(f"ffprobe timed out for {file_path}")
            return {}
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode() if e.stderr else "Unknown error"
            print(f"ffprobe error: {error_msg}")
            return {}
        except json.JSONDecodeError as e:
            print(f"Error parsing ffprobe output: {e}")
            return {}
        except Exception as e:
            print(f"Error getting media info: {str(e)}")
            return {}