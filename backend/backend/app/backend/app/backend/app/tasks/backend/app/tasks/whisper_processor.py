import whisper
import os
from datetime import timedelta

class WhisperProcessor:
    def __init__(self, model_size="base"):
        """
        Initialize Whisper model
        model_size: "tiny", "base", "small", "medium", "large"
        """
        print(f"Loading Whisper {model_size} model...")
        self.model = whisper.load_model(model_size)
        print("Whisper loaded successfully!")
    
    def transcribe(self, video_path):
        """Transcribe video and return segments with timestamps"""
        result = self.model.transcribe(video_path)
        return result
    
    def extract_highlights(self, video_path, min_duration=60, max_duration=120):
        """
        Find the most engaging segments based on:
        - Speech patterns
        - Keyword density
        - Question detection
        - Excitement in voice
        """
        result = self.transcribe(video_path)
        segments = result["segments"]
        
        # Score each segment
        scored_segments = []
        for seg in segments:
            score = 0
            text = seg["text"].lower()
            duration = seg["end"] - seg["start"]
            
            # Skip very short segments
            if duration < 5:
                continue
            
            # Score based on keywords
            keywords = ["amazing", "wow", "important", "key", "secret", 
                       "breakthrough", "incredible", "game changer", "omg",
                       "mind blowing", "crazy", "unbelievable", "shocking"]
            for kw in keywords:
                if kw in text:
                    score += 10
            
            # Score questions (engaging content)
            if "?" in text:
                score += 15
            
            # Score based on exclamation/emphasis
            if "!" in text:
                score += 10
            
            # Score based on segment length
            score += min(duration / 5, 20)
            
            scored_segments.append({
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"],
                "score": score,
                "duration": duration
            })
        
        # Sort by score and merge adjacent segments
        scored_segments.sort(key=lambda x: x["score"], reverse=True)
        
        # Build clips of desired duration
        clips = []
        used_times = set()
        
        for seg in scored_segments:
            # Check if this time range is already used
            time_range = range(int(seg["start"]), int(seg["end"]) + 1)
            if any(t in used_times for t in time_range):
                continue
            
            # Find adjacent high-scoring segments
            clip_start = seg["start"]
            clip_end = seg["end"]
            clip_texts = [seg["text"]]
            
            # Look for nearby segments to extend to min_duration
            for other in scored_segments:
                if other["start"] > clip_end and other["start"] - clip_end < 10:
                    clip_end = other["end"]
                    clip_texts.append(other["text"])
                    for t in range(int(other["start"]), int(other["end"]) + 1):
                        used_times.add(t)
            
            clip_duration = clip_end - clip_start
            
            if clip_duration >= min_duration:
                clips.append({
                    "start": clip_start,
                    "end": clip_end,
                    "duration": clip_duration,
                    "text": " ".join(clip_texts),
                    "score": seg["score"]
                })
                
                # Mark these times as used
                for t in range(int(clip_start), int(clip_end) + 1):
                    used_times.add(t)
            
            # Stop if we have enough clips
            if len(clips) >= 5:
                break
        
        return clips
    
    def generate_srt(self, video_path, output_path):
        """Generate SRT subtitle file"""
        result = self.transcribe(video_path)
        segments = result["segments"]
        
        with open(output_path, 'w', encoding='utf-8') as srt_file:
            for i, seg in enumerate(segments, start=1):
                start_time = str(timedelta(seconds=seg["start"]))
                end_time = str(timedelta(seconds=seg["end"]))
                
                # Format time for SRT
                start_time = start_time.split('.')[0].replace('-', '') + ',000'
                end_time = end_time.split('.')[0].replace('-', '') + ',000'
                
                srt_file.write(f"{i}\n")
                srt_file.write(f"{start_time} --> {end_time}\n")
                srt_file.write(f"{seg['text'].strip()}\n\n")
