import os
import json
import openai
from typing import List, Dict
import subprocess

class AdvancedVoiceoverGenerator:
    """
    Creates different voiceover styles:
    - Solo narrator (existing)
    - Dual host conversation (like NotebookLM)
    - Interview style (Q&A)
    - Debate format (pro/con)
    - Storytelling mode
    """
    
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")
        openai.api_key = self.openai_key
    
    def generate_script(self, transcript_snippet: str, style: str) -> Dict:
        """
        Generate script in different styles
        Returns script with speaker assignments
        """
        
        style_prompts = {
            "solo": """
                Write a solo narrator script that's engaging and informative.
                Speaker: Single host
                Tone: Energetic and clear
                Length: 30-60 seconds
            """,
            
            "dual_host": """
                Write a script for TWO AI hosts having a natural conversation about this content.
                
                Host 1 (Alex): Enthusiastic, asks questions, reacts with excitement
                Host 2 (Jordan): Analytical, provides context, explains concepts
                
                Make it sound like a podcast - natural banter, reactions, back-and-forth.
                Include:
                - Opening banter/introduction
                - Discussion of key points
                - Reactions ("Wow!", "That's amazing!", "Wait, really?")
                - Closing thoughts
                
                Format as: [HOST1]: text | [HOST2]: text
            """,
            
            "interview": """
                Write an interview-style script.
                
                Host: Asks insightful questions, guides conversation
                Expert: Provides answers, explains concepts
                
                Make it sound natural with:
                - Host introduces topic
                - Host asks 3-4 key questions
                - Expert gives detailed answers
                - Host summarizes at end
                
                Format as: [HOST]: text | [EXPERT]: text
            """,
            
            "debate": """
                Write a debate-style script with two perspectives.
                
                Speaker A (Pro): Arguments FOR the main points
                Speaker B (Con): Counter-arguments, alternative views
                Moderator: Introduces topic, manages flow (optional)
                
                Make it engaging with:
                - Opening statements
                - Rebuttals
                - Closing arguments
                
                Format as: [PRO]: text | [CON]: text | [MOD]: text
            """,
            
            "storytelling": """
                Write a storytelling/narrative script.
                
                Narrator: Dramatic, engaging storyteller
                Sound effects: [SFX] markers for ambient sounds
                
                Make it cinematic with:
                - Hook opening
                - Rising tension
                - Climax/reveal
                - Satisfying conclusion
                
                Format as: [NARRATOR]: text with [SFX] markers
            """
        }
        
        prompt = f"""
        {style_prompts.get(style, style_prompts["solo"])}
        
        Based on this transcript from a video clip, create a {style} voiceover script.
        
        Original content: "{transcript_snippet}"
        
        Return as JSON with:
        - script: formatted with speaker markers
        - speakers: list of speaker names
        - duration_estimate: seconds
        - tone: overall tone description
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",  # Using GPT-4 for better conversation quality
                messages=[
                    {"role": "system", "content": "You are an expert scriptwriter for podcasts and videos."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=800
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            # Fallback script
            return {
                "script": f"[HOST1]: Let's talk about this interesting clip. | [HOST2]: I agree, there's so much to discuss!",
                "speakers": ["HOST1", "HOST2"],
                "duration_estimate": 30,
                "tone": "conversational"
            }
    
    def parse_script(self, script_text: str):
        """Parse script with [SPEAKER]: text format"""
        import re
        lines = script_text.split('|')
        parsed = []
        
        for line in lines:
            match = re.match(r'\[(.*?)\]:\s*(.*)', line.strip())
            if match:
                speaker, text = match.groups()
                parsed.append({
                    "speaker": speaker.strip(),
                    "text": text.strip()
                })
        
        return parsed
    
    def generate_multi_speaker_audio(self, parsed_script: List[Dict], output_path: str) -> bool:
        """
        Generate audio with multiple speakers using different voices
        """
        try:
            import tempfile
            from pydub import AudioSegment
            
            audio_segments = []
            speaker_voices = {
                "HOST1": "21m00Tcm4TlvDq8ikWAM",  # Rachel
                "HOST2": "AZnzlk1XvdvUeBnXmlld",  # Domi
                "HOST": "EXAVITQu4vr4xnSDxMaL",   # Sarah
                "EXPERT": "TxGEqnHWrfWFTfGW9XjX", # Josh
                "PRO": "pNInz6obpgDQGcFmaJgB",    # Adam
                "CON": "yoZ06aMxZJJ28mfd3POQ",    # Sam
                "MOD": "XrExE9yKIg1WjnnlVkGX",    # Emily
                "NARRATOR": "MF3mGyEYCl7XYWbV9V6O" # Elli
            }
            
            for segment in parsed_script:
                speaker = segment["speaker"]
                text = segment["text"]
                
                # Choose voice based on speaker
                voice_id = speaker_voices.get(speaker, "21m00Tcm4TlvDq8ikWAM")
                
                # Generate audio for this segment
                temp_file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
                
                from elevenlabs import generate
                audio = generate(
                    text=text,
                    voice=voice_id,
                    model="eleven_monolingual_v1"
                )
                
                with open(temp_file.name, "wb") as f:
                    f.write(audio)
                
                audio_segments.append(AudioSegment.from_mp3(temp_file.name))
                
                # Add small pause between speakers
                if len(parsed_script) > 1:
                    pause = AudioSegment.silent(duration=500)
                    audio_segments.append(pause)
            
            # Combine all segments
            combined = AudioSegment.empty()
            for segment in audio_segments:
                combined += segment
            
            # Export
            combined.export(output_path, format="mp3")
            return True
            
        except Exception as e:
            print(f"Multi-speaker audio failed: {e}")
            return False
    
    def generate_voiceover(self, transcript_snippet: str, style: str, output_path: str) -> Dict:
        """
        Complete pipeline: script generation -> multi-speaker audio
        """
        # Step 1: Generate script in requested style
        script_data = self.generate_script(transcript_snippet, style)
        
        # Step 2: Parse script into speaker segments
        parsed = self.parse_script(script_data['script'])
        
        # Step 3: Generate multi-speaker audio
        success = self.generate_multi_speaker_audio(parsed, output_path)
        
        if success:
            return {
                "success": True,
                "style": style,
                "script": script_data['script'],
                "speakers": script_data['speakers'],
                "audio_path": output_path,
                "duration_estimate": script_data['duration_estimate']
            }
        else:
            return {"success": False, "error": "Audio generation failed"}
