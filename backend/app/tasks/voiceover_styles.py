import os
import json
import openai
from typing import List, Dict
import subprocess
import time

class AdvancedVoiceoverGenerator:
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")
        openai.api_key = self.openai_key
    
    def generate_script(self, transcript_snippet: str, style: str) -> Dict:
        style_prompts = {
            "solo": """
                Write a solo narrator script that's engaging and informative.
                Speaker: Single host
                Tone: Energetic and clear
                Length: 30-60 seconds
            """,
            "dual_host": """
                Write a script for TWO AI hosts having a natural conversation.
                Host 1 (Alex): Enthusiastic, asks questions, reacts
                Host 2 (Jordan): Analytical, provides context
                Make it sound like a podcast – natural banter, reactions.
                Format as: [HOST1]: text | [HOST2]: text
            """,
            "interview": """
                Write an interview-style script.
                Host: Asks insightful questions
                Expert: Provides answers
                Format as: [HOST]: text | [EXPERT]: text
            """,
            "debate": """
                Write a debate-style script.
                Speaker A (Pro): Arguments FOR
                Speaker B (Con): Counter-arguments
                Moderator: Introduces topic (optional)
                Format as: [PRO]: text | [CON]: text | [MOD]: text
            """,
            "storytelling": """
                Write a storytelling/narrative script.
                Narrator: Dramatic, engaging
                Use [SFX] for sound effects.
                Format as: [NARRATOR]: text with [SFX] markers
            """
        }
        prompt = f"""
        {style_prompts.get(style, style_prompts["solo"])}
        Based on this transcript: "{transcript_snippet}"
        Return as JSON with:
        - script: formatted with speaker markers
        - speakers: list of speaker names
        - duration_estimate: seconds
        - tone: overall tone
        """
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert scriptwriter."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=800
            )
            result = json.loads(response.choices[0].message.content)
            return result
        except:
            return {
                "script": "[HOST1]: Let's talk about this. | [HOST2]: I agree!",
                "speakers": ["HOST1", "HOST2"],
                "duration_estimate": 30,
                "tone": "conversational"
            }
    
    def parse_script(self, script_text: str):
        import re
        lines = script_text.split('|')
        parsed = []
        for line in lines:
            match = re.match(r'\[(.*?)\]:\s*(.*)', line.strip())
            if match:
                speaker, text = match.groups()
                parsed.append({"speaker": speaker.strip(), "text": text.strip()})
        return parsed
    
    def generate_multi_speaker_audio(self, parsed_script: List[Dict], output_path: str) -> bool:
        try:
            import tempfile
            from pydub import AudioSegment
            from elevenlabs import generate
            audio_segments = []
            speaker_voices = {
                "HOST1": "21m00Tcm4TlvDq8ikWAM",  # Rachel
                "HOST2": "AZnzlk1XvdvUeBnXmlld",  # Domi
                "HOST": "EXAVITQu4vr4xnSDxMaL",    # Sarah
                "EXPERT": "TxGEqnHWrfWFTfGW9XjX",  # Josh
                "PRO": "pNInz6obpgDQGcFmaJgB",      # Adam
                "CON": "yoZ06aMxZJJ28mfd3POQ",      # Sam
                "MOD": "XrExE9yKIg1WjnnlVkGX",      # Emily
                "NARRATOR": "MF3mGyEYCl7XYWbV9V6O"  # Elli
            }
            for segment in parsed_script:
                speaker = segment["speaker"]
                text = segment["text"]
                voice_id = speaker_voices.get(speaker, "21m00Tcm4TlvDq8ikWAM")
                temp_file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
                audio = generate(text=text, voice=voice_id, model="eleven_monolingual_v1")
                with open(temp_file.name, "wb") as f:
                    f.write(audio)
                audio_segments.append(AudioSegment.from_mp3(temp_file.name))
                if len(parsed_script) > 1:
                    audio_segments.append(AudioSegment.silent(duration=500))
            combined = AudioSegment.empty()
            for seg in audio_segments:
                combined += seg
            combined.export(output_path, format="mp3")
            return True
        except Exception as e:
            print(f"Multi-speaker audio failed: {e}")
            return False
    
    def generate_voiceover(self, transcript_snippet: str, style: str, output_path: str) -> Dict:
        script_data = self.generate_script(transcript_snippet, style)
        parsed = self.parse_script(script_data['script'])
        success = self.generate_multi_speaker_audio(parsed, output_path)
        if success:
            return {
                'success': True,
                'style': style,
                'script': script_data['script'],
                'speakers': script_data['speakers'],
                'audio_path': output_path,
                'duration_estimate': script_data['duration_estimate']
            }
        else:
            return {'success': False, 'error': 'Audio generation failed'}
