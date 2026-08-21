import math
from django.conf import settings

class ChunkingService:
    def __init__(self):
        self.chunk_size = getattr(settings, 'CHUNK_SIZE', 1000)
        self.overlap = getattr(settings, 'CHUNK_OVERLAP', 200)

    def _estimate_tokens(self, text: str) -> int:
        """Estimate tokens, ensuring short non-empty text counts as at least 1 token."""
        if not text:
            return 0
        return math.ceil(len(text) / 4)

    def create_chunks(self, segments: list, chunk: bool = True) -> list:
        if not segments:
            return []

        # Bypass chunking loop and return the entire transcript as a single chunk
        if not chunk:
            return [self._build_chunk(segments)]

        chunks = []
        current_chunk = []
        current_tokens = 0

        for segment in segments:
            segment_tokens = self._estimate_tokens(segment['text'])

            # Handle edge case: single segment larger than entire chunk_size
            if segment_tokens > self.chunk_size:
                if current_chunk:
                    chunks.append(self._build_chunk(current_chunk))
                    current_chunk = []
                    current_tokens = 0
                chunks.append(self._build_chunk([segment]))
                continue

            # Check if adding segment exceeds limit
            if current_tokens + segment_tokens > self.chunk_size and current_chunk:
                chunks.append(self._build_chunk(current_chunk))

                overlap_segments = []
                overlap_tokens = 0
                for seg in reversed(current_chunk):
                    seg_tokens = self._estimate_tokens(seg['text'])
                    if overlap_tokens + seg_tokens <= self.overlap or not overlap_segments:
                        overlap_segments.insert(0, seg)
                        overlap_tokens += seg_tokens
                    else:
                        break

                current_chunk = overlap_segments.copy()
                current_tokens = overlap_tokens

            current_chunk.append(segment)
            current_tokens += segment_tokens

        if current_chunk:
            chunks.append(self._build_chunk(current_chunk))

        return chunks

    def _build_chunk(self, segments: list) -> dict:
        """
        Formats segments into line-by-line timestamped strings so the LLM has
        exact temporal context for every spoken sentence.
        """
        formatted_lines = [
            f"[{float(s['start']):.2f}s - {float(s['end']):.2f}s] {s['text'].strip()}"
            for s in segments
        ]

        return {
            'segments': segments.copy(),
            'text': '\n'.join(formatted_lines),
            'start': segments[0]['start'],
            'end': segments[-1]['end']
        }

    def align_clip_timestamps(self, ai_start: float, ai_end: float, segments: list, padding: float = 0.2) -> dict:
        """
        Snaps AI-generated timestamps back to exact Whisper/audio segment boundaries 
        and adds a small pre/post-roll padding buffer to avoid mid-word cuts.
        """
        if not segments:
            return {'start': ai_start, 'end': ai_end}

        closest_start_segment = min(segments, key=lambda s: abs(s['start'] - ai_start))
        snapped_start = max(0.0, float(closest_start_segment['start']) - padding)

        closest_end_segment = min(segments, key=lambda s: abs(s['end'] - ai_end))
        snapped_end = float(closest_end_segment['end']) + padding

        return {
            'start': round(snapped_start, 2),
            'end': round(snapped_end, 2)
        }