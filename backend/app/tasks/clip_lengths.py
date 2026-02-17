import subprocess
import os

class MultiLengthClipProcessor:
    def __init__(self, output_dir="./clips"):
        self.output_dir = output_dir
    
    def extract_teaser(self, video_path, start_time, end_time, output_path, clip_id):
        try:
            duration = min(end_time - start_time, 30)
            peak_time = start_time + (duration / 2)
            cmd = [
                'ffmpeg', '-i', video_path,
                '-ss', str(peak_time - 7.5),
                '-t', '15',
                '-c:v', 'libx264', '-c:a', 'aac',
                '-vf', 'scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280',
                '-movflags', '+faststart',
                '-y', output_path
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            return {
                "success": True,
                "path": output_path,
                "duration": 15,
                "type": "teaser"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def extract_standard(self, video_path, start_time, end_time, output_path):
        try:
            duration = min(end_time - start_time, 60)
            cmd = [
                'ffmpeg', '-i', video_path,
                '-ss', str(start_time),
                '-t', str(duration),
                '-c:v', 'libx264', '-c:a', 'aac',
                '-b:v', '2000k', '-b:a', '128k',
                '-movflags', '+faststart',
                '-y', output_path
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            return {
                "success": True,
                "path": output_path,
                "duration": duration,
                "type": "standard"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def extract_explainer(self, video_path, start_time, end_time, output_path, transcript_snippet):
        try:
            extended_start = max(0, start_time - 30)
            extended_end = min(end_time + 30, end_time + 90)
            duration = extended_end - extended_start
            if duration > 180:
                duration = 180
                extended_end = extended_start + 180
            cmd = [
                'ffmpeg', '-i', video_path,
                '-ss', str(extended_start),
                '-t', str(duration),
                '-c:v', 'libx264', '-c:a', 'aac',
                '-b:v', '2500k', '-b:a', '160k',
                '-movflags', '+faststart',
                '-y', output_path
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            return {
                "success": True,
                "path": output_path,
                "duration": duration,
                "type": "explainer",
                "start": extended_start,
                "end": extended_end
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def extract_all_lengths(self, video_path, clip_data, video_id):
        output_dir = os.path.join(self.output_dir, video_id)
        os.makedirs(output_dir, exist_ok=True)
        results = []
        for clip in clip_data:
            clip_id = clip['id']
            start = clip['start_time']
            end = clip['end_time']
            transcript = clip.get('text_snippet', '')
            clip_results = {"clip_id": clip_id, "lengths": {}}
            teaser_path = os.path.join(output_dir, f"clip_{clip_id:03d}_teaser.mp4")
            teaser = self.extract_teaser(video_path, start, end, teaser_path, clip_id)
            if teaser['success']:
                clip_results['lengths']['teaser'] = teaser
            standard_path = os.path.join(output_dir, f"clip_{clip_id:03d}_standard.mp4")
            standard = self.extract_standard(video_path, start, end, standard_path)
            if standard['success']:
                clip_results['lengths']['standard'] = standard
            explainer_path = os.path.join(output_dir, f"clip_{clip_id:03d}_explainer.mp4")
            explainer = self.extract_explainer(video_path, start, end, explainer_path, transcript)
            if explainer['success']:
                clip_results['lengths']['explainer'] = explainer
            results.append(clip_results)
        return results
