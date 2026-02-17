from app.celery_app import celery
from app.tasks.whisper_processor import WhisperProcessor
from app.tasks.thumbnail_generator import ThumbnailGenerator
from app.tasks.clip_processor import ClipProcessor
from app.tasks.title_generator import TitleGenerator
from app.tasks.voiceover_styles import AdvancedVoiceoverGenerator
from app.tasks.thumbnail_styles import ThumbnailStylist
from app.tasks.clip_lengths import MultiLengthClipProcessor
import os
import json

# Initialize processors
whisper = WhisperProcessor(model_size="base")
thumbnail_gen = ThumbnailGenerator()
clip_processor = ClipProcessor(output_dir="./clips")
title_gen = TitleGenerator()
advanced_voiceover = AdvancedVoiceoverGenerator()
thumbnail_stylist = ThumbnailStylist()
multi_length_clips = MultiLengthClipProcessor()

@celery.task(bind=True)
def process_video(self, video_path: str):
    try:
        video_id = os.path.basename(video_path).split('.')[0]
        
        # === STAGE 1: WHISPER ANALYSIS ===
        self.update_state(state='PROCESSING', meta={'stage': 'analyzing with Whisper AI'})
        highlights = whisper.extract_highlights(video_path, min_duration=60, max_duration=120)
        
        # === STAGE 2: CAPTIONS ===
        self.update_state(state='PROCESSING', meta={'stage': 'generating captions'})
        captions_dir = "./captions"
        os.makedirs(captions_dir, exist_ok=True)
        srt_path = os.path.join(captions_dir, f"{video_id}.srt")
        whisper.generate_srt(video_path, srt_path)
        
        # === STAGE 3: BASIC THUMBNAILS ===
        self.update_state(state='PROCESSING', meta={'stage': 'generating thumbnails'})
        thumbnails_dir = f"./thumbnails/{video_id}"
        clip_thumbnails = thumbnail_gen.generate_clip_thumbnails(video_path, highlights, thumbnails_dir)
        
        # === STAGE 4: EXTRACT VIDEO CLIPS ===
        self.update_state(state='PROCESSING', meta={'stage': 'extracting video clips'})
        clip_data = [{'id': i+1, 'start_time': h['start'], 'end_time': h['end'], 'text_snippet': h['text'], 'ai_score': h['score']}
                     for i, h in enumerate(highlights)]
        clip_results = clip_processor.extract_multiple_clips(video_path, clip_data, video_id)
        
        # === STAGE 5: GENERATE AI TITLES ===
        self.update_state(state='PROCESSING', meta={'stage': 'generating AI titles'})
        clip_titles = []
        for i, (highlight, clip_file) in enumerate(zip(highlights, clip_results)):
            if clip_file['success']:
                titles = title_gen.generate_titles(highlight['text'][:300], clip_file['duration'], highlight['score'], n=3)
                description = title_gen.generate_description(highlight['text'][:500], titles[0]['title'] if titles else f"Clip {i+1}")
                hashtags = title_gen.generate_hashtags(highlight['text'][:300])
                clip_titles.append({
                    'clip_id': i+1,
                    'titles': titles,
                    'best_title': titles[0]['title'] if titles else f"Clip {i+1}",
                    'description': description,
                    'hashtags': hashtags
                })
        
        # === STAGE 6: MULTI‑LENGTH CLIPS ===
        self.update_state(state='PROCESSING', meta={'stage': 'creating multiple clip lengths'})
        multi_length_results = multi_length_clips.extract_all_lengths(video_path, clip_data, video_id)
        
        # === STAGE 7: STYLED VOICEOVERS (for top 2 clips, 2 styles each) ===
        self.update_state(state='PROCESSING', meta={'stage': 'generating advanced voiceovers'})
        voiceover_results = []
        voiceover_styles = ["solo", "dual_host", "interview", "debate", "storytelling"]
        voiceovers_dir = f"./voiceovers/{video_id}"
        os.makedirs(voiceovers_dir, exist_ok=True)
        for i, highlight in enumerate(highlights[:2]):
            for style in voiceover_styles[:2]:
                audio_path = os.path.join(voiceovers_dir, f"clip_{i+1}_{style}.mp3")
                result = advanced_voiceover.generate_voiceover(highlight['text'], style, audio_path)
                if result['success']:
                    voiceover_results.append({'clip_id': i+1, 'style': style, 'audio_path': audio_path, 'script': result['script']})
        
        # === STAGE 8: STYLED THUMBNAILS (for top 3 clips, 3 styles each) ===
        self.update_state(state='PROCESSING', meta={'stage': 'generating AI thumbnails'})
        thumbnail_styles = ["cinematic", "anime", "watercolor", "retro_print", "whiteboard", "clickbait"]
        styled_thumbnails = []
        for i, highlight in enumerate(highlights[:3]):
            for style in thumbnail_styles[:3]:
                thumb_path = os.path.join(thumbnails_dir, f"clip_{i+1}_{style}.jpg")
                success = thumbnail_stylist.generate_ai_thumbnail(highlight['text'], style, thumb_path)
                if success:
                    title = clip_titles[i]['best_title'] if i < len(clip_titles) else f"Clip {i+1}"
                    thumbnail_stylist.add_text_overlay(thumb_path, title)
                    styled_thumbnails.append({
                        'clip_id': i+1,
                        'style': style,
                        'path': thumb_path,
                        'web_path': thumb_path.replace('.jpg', '_web.jpg')
                    })
        
        # === STAGE 9: COMBINE RESULTS ===
        self.update_state(state='PROCESSING', meta={'stage': 'finalizing results'})
        clips = []
        for i, (highlight, thumb, clip_file, title_data) in enumerate(zip(highlights, clip_thumbnails, clip_results, clip_titles)):
            if clip_file['success']:
                clip_multi = next((m for m in multi_length_results if m['clip_id'] == i+1), None)
                clip_voiceovers = [vo for vo in voiceover_results if vo['clip_id'] == i+1]
                clip_styled_thumbs = [st for st in styled_thumbnails if st['clip_id'] == i+1]
                clip_info = {
                    "id": i+1,
                    "start_time": highlight["start"],
                    "end_time": highlight["end"],
                    "duration": clip_file['duration'],
                    "ai_score": highlight["score"],
                    "text_snippet": highlight["text"][:200] + "...",
                    "titles": title_data['titles'],
                    "best_title": title_data['best_title'],
                    "description": title_data['description'],
                    "hashtags": title_data['hashtags'],
                    "thumbnail": {
                        "path": thumb['path'],
                        "web_path": thumb['web_path'],
                        "time": thumb['time'],
                        "has_faces": thumb['has_faces']
                    },
                    "styled_thumbnails": clip_styled_thumbs,
                    "voiceover_options": clip_voiceovers,
                    "multi_length": clip_multi['lengths'] if clip_multi else {},
                    "video_file": {
                        "path": clip_file['path'],
                        "web_path": clip_file['web_path'],
                        "size": os.path.getsize(clip_file['path']) if os.path.exists(clip_file['path']) else 0
                    }
                }
                clips.append(clip_info)
        
        return {
            "status": "completed",
            "video_id": video_id,
            "video_path": video_path,
            "captions_file": srt_path,
            "thumbnails_dir": thumbnails_dir,
            "voiceovers_dir": voiceovers_dir,
            "clips_dir": f"./clips/{video_id}",
            "clips": clips,
            "total_clips": len(clips),
            "stats": {
                "total_duration": sum(c['duration'] for c in clips),
                "avg_score": sum(c['ai_score'] for c in clips) / len(clips) if clips else 0,
                "has_faces": any(c['thumbnail']['has_faces'] for c in clips),
                "voiceovers_generated": len(voiceover_results),
                "styled_thumbnails": len(styled_thumbnails)
            },
            "message": f"✅ Complete! Generated {len(clips)} clips with AI titles, voiceovers, and styled thumbnails"
        }
    except Exception as e:
        import traceback
        return {
            "status": "failed",
            "error": str(e),
            "traceback": traceback.format_exc(),
            "message": f"❌ Processing failed: {str(e)}"
        }
