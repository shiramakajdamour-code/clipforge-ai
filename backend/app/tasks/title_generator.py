import openai
import os
from typing import List, Dict

class TitleGenerator:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        openai.api_key = self.api_key
    
    def generate_titles(self, transcript_snippet: str, clip_duration: float, ai_score: float, n=3) -> List[Dict]:
        prompt = f"""
        You are a professional video title writer for YouTube, TikTok, and Instagram.
        Based on this transcript snippet from a video clip, generate {n} engaging, click-worthy titles.
        Transcript: "{transcript_snippet}"
        Clip duration: {clip_duration:.0f} seconds
        AI quality score: {ai_score}/100
        Rules:
        - Titles should be 40-60 characters
        - Use power words
        - Include numbers if relevant
        - Create curiosity gaps
        - Optimize for different platforms
        Return as JSON array with title, platform_focus, and predicted_ctr (0-100).
        """
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert video title writer. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=500
            )
            import json
            titles = json.loads(response.choices[0].message.content)
            return titles
        except Exception as e:
            return [
                {"title": f"Amazing Clip (Score: {ai_score})", "platform_focus": "general", "predicted_ctr": 50},
                {"title": "You Won't Believe This", "platform_focus": "tiktok", "predicted_ctr": 45},
                {"title": "Secret Revealed 🔥", "platform_focus": "instagram", "predicted_ctr": 40}
            ]
    
    def generate_description(self, transcript_snippet: str, title: str, tags=None) -> str:
        prompt = f"""
        Write a compelling YouTube video description for a clip titled: "{title}"
        Based on this transcript: "{transcript_snippet}"
        Include:
        - Engaging first sentence
        - 2-3 paragraph breakdown
        - Relevant hashtags (5-10)
        - Call to action
        Return as plain text.
        """
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert video description writer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Check out this amazing clip! {transcript_snippet[:100]}... #viral #trending"
    
    def generate_hashtags(self, transcript_snippet: str, n=10) -> List[str]:
        prompt = f"""
        Generate {n} relevant hashtags for social media based on this content:
        "{transcript_snippet}"
        Return as comma-separated list.
        """
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a social media hashtag expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6,
                max_tokens=150
            )
            tags = response.choices[0].message.content.strip().split(',')
            return [tag.strip() for tag in tags if tag.strip()]
        except Exception as e:
            return ["#viral", "#trending", "#fyp", "#video", "#clip", "#amazing", "#mustwatch", "#shorts", "#reels", "#tiktok"]
