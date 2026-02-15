import os
import openai
import replicate
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import requests
from io import BytesIO

class ThumbnailStylist:
    """
    Applies different visual styles to thumbnails:
    - Watercolor (artistic, soft)
    - Anime (vibrant, stylized)
    - Whiteboard (clean, educational)
    - Retro Print (vintage, textured)
    - Paper-Craft (layered, handmade)
    - Cinematic (dramatic, movie-style)
    - Clickbait (bright, high-contrast)
    """
    
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.replicate_token = os.getenv("REPLICATE_API_TOKEN")
        openai.api_key = self.openai_key
    
    def generate_context_description(self, transcript_snippet: str) -> str:
        """Create detailed image prompt from transcript"""
        prompt = f"""
        Create a detailed image description for a YouTube thumbnail based on this transcript.
        
        Transcript: "{transcript_snippet}"
        
        Include:
        - Main subject/theme
        - Key objects/people
        - Mood/emotion
        - Colors that would work well
        
        Return a single paragraph description perfect for AI image generation.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You create detailed image descriptions for thumbnails."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=150
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"A scene about: {transcript_snippet[:100]}"
    
    def apply_style_prompt(self, base_description: str, style: str) -> str:
        """Enhance description with style-specific prompts"""
        
        style_prompts = {
            "watercolor": """
                Style: Watercolor painting
                Artistic, soft edges, flowing colors, painterly texture,
                gentle gradients, artistic impression, beautiful washes of color,
                painted on textured paper, professional art style
            """,
            
            "anime": """
                Style: Anime/Manga
                Vibrant colors, cel-shaded, large expressive eyes if people,
                dynamic composition, clean lines, Japanese animation style,
                dramatic lighting, energetic, Studio Ghibli inspired
            """,
            
            "whiteboard": """
                Style: Whiteboard animation
                Clean lines, simple shapes, educational style, hand-drawn look,
                marker on white background, instructional design,
                minimal colors (mostly black, blue, red, green)
            """,
            
            "retro_print": """
                Style: Retro vintage print
                Aged paper texture, faded colors, halftone dots, screen printing look,
                1970s/80s aesthetic, warm tones, slightly distressed,
                classic poster style with character
            """,
            
            "paper_craft": """
                Style: Paper-craft
                Layered paper cutouts, dimensional, shadow depth, handmade feel,
                textured paper, origami elements, craft aesthetic,
                realistic paper shadows and layers
            """,
            
            "cinematic": """
                Style: Cinematic movie poster
                Dramatic lighting, deep shadows, rich colors, epic scale,
                Hollywood production quality, film grain, anamorphic lens look,
                blockbuster movie poster aesthetic
            """,
            
            "clickbait": """
                Style: YouTube clickbait thumbnail
                Ultra bright colors, high contrast, bold text space reserved,
                surprised expressions if people, arrows and highlights,
                eye-catching, maximum click-through rate optimized,
                YouTube algorithm friendly
            """
        }
        
        return f"{base_description}\n\n{style_prompts.get(style, style_prompts['cinematic'])}"
    
    def generate_ai_thumbnail(self, transcript_snippet: str, style: str, output_path: str) -> bool:
        """
        Generate AI-powered thumbnail based on transcript content
        """
        # Step 1: Get context description
        context = self.generate_context_description(transcript_snippet)
        
        # Step 2: Apply style
        full_prompt = self.apply_style_prompt(context, style)
        
        # Step 3: Add text overlay instructions
        full_prompt += "\n\nLeave space at top and bottom for text overlay. Vertical orientation 1280x720."
        
        try:
            # Try DALL-E 3 first
            response = openai.Image.create(
                model="dall-e-3",
                prompt=full_prompt[:1000],  # DALL-E has limit
                size="1792x1024",  # Close to 16:9
                quality="hd",
                n=1
            )
            
            # Download image
            image_url = response.data[0].url
            img_response = requests.get(image_url)
            img = Image.open(BytesIO(img_response.content))
            
            # Resize to standard thumbnail size
            img = img.resize((1280, 720), Image.Resampling.LANCZOS)
            
            # Apply style-specific post-processing
            img = self.apply_style_postprocess(img, style)
            
            # Save
            img.save(output_path, "JPEG", quality=95)
            
            # Also create web version
            web_path = output_path.replace('.jpg', '_web.jpg')
            web_img = img.resize((640, 360), Image.Resampling.LANCZOS)
            web_img.save(web_path, "JPEG", quality=85)
            
            return True
            
        except Exception as e:
            print(f"AI thumbnail generation failed: {e}")
            
            # Fallback to Replicate (Stable Diffusion)
            try:
                import replicate
                
                output = replicate.run(
                    "stability-ai/stable-diffusion:db21e45d3f7023abc2a46ee38a23973f6dce16bb082a930b0c49861f96d1e5bf",
                    input={
                        "prompt": full_prompt,
                        "width": 1280,
                        "height": 720,
                        "num_outputs": 1,
                        "scheduler": "DPMSolverMultistep"
                    }
                )
                
                img_response = requests.get(output[0])
                img = Image.open(BytesIO(img_response.content))
                img.save(output_path, "JPEG", quality=95)
                
                web_path = output_path.replace('.jpg', '_web.jpg')
                web_img = img.resize((640, 360), Image.Resampling.LANCZOS)
                web_img.save(web_path, "JPEG", quality=85)
                
                return True
                
            except Exception as e2:
                print(f"Replicate also failed: {e2}")
                return False
    
    def apply_style_postprocess(self, img: Image, style: str) -> Image:
        """Apply additional post-processing based on style"""
        
        if style == "watercolor":
            # Soft, painterly effect
            img = img.filter(ImageFilter.SMOOTH_MORE)
            
        elif style == "retro_print":
            # Add grain and slight fade
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(0.8)
            
        elif style == "cinematic":
            # Add letterbox bars
            draw = ImageDraw.Draw(img)
            draw.rectangle([(0, 0), (1280, 60)], fill="black")
            draw.rectangle([(0, 660), (1280, 720)], fill="black")
            
        elif style == "clickbait":
            # Boost contrast and saturation
            from PIL import ImageEnhance
            contrast = ImageEnhance.Contrast(img)
            img = contrast.enhance(1.2)
            color = ImageEnhance.Color(img)
            img = color.enhance(1.3)
        
        return img
    
    def add_text_overlay(self, thumbnail_path: str, title: str, output_path: str = None):
        """Add title text to thumbnail"""
        try:
            img = Image.open(thumbnail_path)
            draw = ImageDraw.Draw(img)
            
            # Try to load a font, fallback to default
            try:
                font = ImageFont.truetype("Arial Bold.ttf", 60)
                small_font = ImageFont.truetype("Arial.ttf", 30)
            except:
                font = ImageFont.load_default()
                small_font = font
            
            # Add gradient overlay for text
            overlay = Image.new('RGBA', img.size, (0,0,0,0))
            overlay_draw = ImageDraw.Draw(overlay)
            
            # Semi-transparent bar at bottom
            overlay_draw.rectangle(
                [(0, 520), (1280, 720)], 
                fill=(0, 0, 0, 180)
            )
            
            img = Image.alpha_composite(img.convert('RGBA'), overlay)
            draw = ImageDraw.Draw(img)
            
            # Add title text
            words = title.split()
            line1 = " ".join(words[:4])
            line2 = " ".join(words[4:8]) if len(words) > 4 else ""
            
            # Text with stroke effect
            text_color = (255, 255, 255)
            stroke_color = (0, 0, 0)
            
            # Draw text twice for stroke effect
            for offset in [(2,2), (-2,-2), (2,-2), (-2,2), (0,0)]:
                x_offset, y_offset = offset
                if offset == (0,0):
                    draw_color = text_color
                else:
                    draw_color = stroke_color
                
                draw.text((100 + x_offset, 560 + y_offset), line1, 
                         font=font, fill=draw_color)
                if line2:
                    draw.text((100 + x_offset, 630 + y_offset), line2, 
                             font=small_font, fill=draw_color)
            
            # Save
            if output_path:
                img.save(output_path, "JPEG", quality=95)
            else:
                img.save(thumbnail_path, "JPEG", quality=95)
            
            return True
            
        except Exception as e:
            print(f"Text overlay failed: {e}")
            return False
