import ffmpeg
import os
import subprocess

class ClipProcessor:
    def __init__(self, output_dir="./clips"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def extract_clip(self, video_path, start_time, end_time, output_path, clip_id):
        """
        Extract a clip from video using FFmpeg
        """
        try:
            # Calculate duration
            duration = end_time - start_time
            
            # Ensure minimum 60 seconds
            if duration < 60:
                # Extend to 60 seconds if possible
                end_time = start_time + 60
                duration = 60
            
            # Format times for FFmpeg
            start_str = self._format_time(start_time)
            duration_str = self._format_time(duration)
            
            # Build FFmpeg command for high-quality clip
            (
                ffmpeg
                .input(video_path, ss=start_str, t=duration_str)
                .output(
                    output_path,
                    vcodec='libx264',
                    acodec='aac',
                    video_bitrate='2000k',
                    audio_bitrate='128k',
                    preset='fast',
                    movflags='+faststart'
                )
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            
            # Also create a smaller version for web/preview
            web_path = output_path.replace('.mp4', '_web.mp4')
            self._create_web_version(output_path, web_path)
            
            return {
                'success': True,
                'path': output_path,
                'web_path': web_path,
                'duration': duration,
                'start': start_time,
                'end': end_time
            }
            
        except ffmpeg.Error as e:
            return {
                'success': False,
                'error': e.stderr.decode(),
                'path': None
            }
    
    def _format_time(self, seconds):
        """Convert seconds to HH:MM:SS.mmm format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds_remainder = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds_remainder:06.3f}"
    
    def _create_web_version(self, input_path, output_path, target_size='720x1280'):
        """
        Create mobile-optimized version for TikTok/Reels/Shorts
        """
        try:
            # Create vertical version for mobile
            (
                ffmpeg
                .input(input_path)
                .filter('scale', 720, 1280, force_original_aspect_ratio='increase')
                .filter('crop', 720, 1280)
                .output(
                    output_path,
                    vcodec='libx264',
                    acodec='aac',
                    video_bitrate='1000k',
                    preset='fast',
                    movflags='+faststart'
                )
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            return True
        except:
            # Fallback to horizontal version
            try:
                (
                    ffmpeg
                    .input(input_path)
                    .output(
                        output_path,
                        vcodec='libx264',
                        acodec='aac',
                        video_bitrate='1000k',
                        preset='fast'
                    )
                    .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True)
                )
                return True
            except:
                return False
    
    def extract_multiple_clips(self, video_path, clips, video_id):
        """
        Extract multiple clips from a video
        clips: list of dict with start_time, end_time, id
        """
        output_dir = os.path.join(self.output_dir, video_id)
        os.makedirs(output_dir, exist_ok=True)
        
        results = []
        for clip in clips:
            clip_id = clip['id']
            output_path = os.path.join(output_dir, f"clip_{clip_id:03d}.mp4")
            
            result = self.extract_clip(
                video_path,
                clip['start_time'],
                clip['end_time'],
                output_path,
                clip_id
            )
            
            result['clip_id'] = clip_id
            result['metadata'] = {
                'title': f"Clip {clip_id}",
                'description': clip.get('text_snippet', '')[:100],
                'duration': result.get('duration', 0),
                'score': clip.get('ai_score', 0)
            }
            
            results.append(result)
        
        return results
