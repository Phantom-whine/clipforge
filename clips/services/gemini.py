# clips/services/gemini.py
import google.generativeai as genai
from django.conf import settings
import json
import re

class GeminiService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-3.6-flash')
    
    def analyze_chunks(self, chunks: list, project_settings: dict) -> list:
        """
        Analyze transcription chunks and extract clip recommendations
        Returns list of clip recommendations with metadata
        """
        all_clips = []
        
        for chunk in chunks:
            clips = self._analyze_chunk(chunk, project_settings)
            all_clips.extend(clips)
        
        # Sort by overall score and take top N based on clip_count
        all_clips.sort(key=lambda x: x['overall_score'], reverse=True)
        
        # Determine how many clips to return
        clip_count = project_settings.get('clip_count', 'balanced')
        if clip_count == 'balanced':
            target_count = len(all_clips) // 2
        else:
            target_count = int(clip_count)
        
        return all_clips[:target_count]
    
    def _analyze_chunk(self, chunk: dict, project_settings: dict) -> list:
        """Analyze a single chunk and return clip recommendations"""
        
        moment_types = project_settings.get('moment_types', [])
        target_duration = project_settings.get('target_duration', '30-60')
        description = project_settings.get('description', '').strip()
        context_section = description or 'No additional context was provided by the user.'
        
        prompt = f"""
You are an expert short-form video editor and content strategist. Analyze the provided transcription to identify complete, self-contained moments that are optimized for short-form platforms (TikTok, Reels, Shorts).

TRANSCRIPTION CHUNK (from {chunk['start']:.2f}s to {chunk['end']:.2f}s):
{chunk['text']}

TARGET SETTINGS:
- Target clip duration: {target_duration} seconds
- Priority moment types: {', '.join(moment_types) if moment_types else 'all types'}

USER-PROVIDED CONTENT CONTEXT:
{context_section}

Use this context to understand the video's subject, audience, goals, or brand. Treat it as helpful background, not as a replacement for the transcript. Prefer clips that support the stated context while still meeting every boundary and self-containment rule below.

CRITICAL GUIDELINES FOR CLIP BOUNDARIES:
1. Immediate Hook: The start timestamp MUST begin at a clear, attention-grabbing statement or sentence opening. Do not start mid-sentence, mid-word, or mid-thought.
2. Complete Narrative Arc: The clip MUST contain a full, coherent point. The end timestamp MUST conclude at the natural end of a sentence or thought where the core message is fully resolved.
3. Strict Self-Containment: The clip must NOT feel cut off, abrupt, half-baked, or incomplete. A viewer watching this clip in isolation must fully understand the key takeaway without requiring any prior or subsequent context.
4. Topic Isolation: Do NOT mix unrelated topics or jump across different context boundaries in the transcription. Ensure each selected clip focuses strictly on a single, continuous idea from start to finish.
5. The Video topics should also align with Gen Z and Millennial interests, including but not limited to: pop culture, trending topics, humor, lifestyle, personal growth, and relatable experiences.
6. The title should be catchy, you can also use humor, puns or Gen Z slang to make it more engaging. Keep it under 10 words.

For each clip, provide:
1. A catchy title (max 10 words)
2. Exact start and end timestamps (relative to the original video)
3. A short explanation of why this clip works well
4. Scores (0-100) for:
   - Hook strength: How strong and immediate is the opening statement?
   - Curiosity: Does it spark instant viewer engagement?
   - Standalone: Is the idea 100% complete with zero missing context?
   - Value: Educational or practical payoff
   - Entertainment: General engagement level
5. Overall score (average of the above)

Return a JSON array using this exact structure:
[
  {{
    "title": "string",
    "start_time": float,
    "end_time": float,
    "why_this_clip": "string",
    "hook_strength": int,
    "curiosity": int,
    "standalone": int,
    "value": int,
    "entertainment": int,
    "overall_score": int
  }}
]

Identify 2-4 clips from this chunk. Return ONLY valid JSON—no markdown code blocks, no intro, and no outro text.
"""
        
        try:
            response = self.model.generate_content(prompt)
            
            # Extract JSON from response
            json_str = self._extract_json(response.text)
            clips = json.loads(json_str)
            
            # Validate and clean clips
            validated_clips = []
            for clip in clips:
                if self._validate_clip(clip, chunk):
                    validated_clips.append(clip)
            
            return validated_clips
            
        except Exception as e:
            print(f"Error analyzing chunk: {e}")
            return []
    
    def _extract_json(self, text: str) -> str:
        """Extract JSON from Gemini response"""
        # Try to find JSON array in the text
        match = re.search(r'\[[\s\S]*\]', text)
        if match:
            return match.group()
        return text
    
    def _validate_clip(self, clip: dict, chunk: dict) -> bool:
        """Validate clip data structure and timestamps"""
        required_fields = ['title', 'start_time', 'end_time', 'why_this_clip',
                          'hook_strength', 'curiosity', 'standalone', 'value',
                          'entertainment', 'overall_score']
        
        if not all(field in clip for field in required_fields):
            return False
        
        # Ensure timestamps are within chunk range
        if not (chunk['start'] <= clip['start_time'] <= chunk['end']):
            return False
        if not (chunk['start'] <= clip['end_time'] <= chunk['end']):
            return False
        
        # Ensure end > start
        if clip['end_time'] <= clip['start_time']:
            return False
        
        return True