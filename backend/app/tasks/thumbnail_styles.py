import os
import openai
import replicate
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import requests
from io import BytesIO

class ThumbnailStylist:
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.replicate_token = os.getenv("REPLICATE_API_TOKEN")
        openai.api_key = self.openai_key
    
    def generate_context_description(self, transcript_snippet: str) -> str:
        prompt = f"""
        Create a detailed image description for a YouTube thumbnail based on this transcript.
        Transcript: "{transcript_snippet}"
        Include:
        - Main subject/theme
        - Key objects/people
        - Mood/emotion
        - Colors that would work well
        Return a single paragraph description.
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
        except:
            return f"A scene about: {transcript_snippet[:100]}"
    
    def apply_style_prompt(self, base_description: str, style: str) -> str:
        style_prompts = {
            "watercolor": "Style: Watercolor painting, soft edges, flowing colors, painterly texture, artistic impression.",
            "anime": "Style: Anime/Manga, vibrant colors, cel-shaded, large expressive eyes, dynamic composition.",
            "whiteboard": "Style: Whiteboard animation, clean lines, simple shapes, educational style, hand-drawn look.",
            "retro_print": "Style: Retro vintage print, aged paper texture, faded colors, halftone dots, 70s aesthetic.",
            "paper_craft": "Style: Paper-craft, layered paper cutouts, dimensional, handmade feel, textured paper.",
            "cinematic": "Style: Cinematic movie poster, dramatic lighting, deep shadows, rich colors, epic scale.",
            "clickbait": "Style: YouTube clickbait, ultra bright colors, high contrast, surprised expressions, arrows."
        }
        return f"{base_description}\n\n{style_prompts.get(style, style_prompts['cinematic'])}"
    
    def generate_ai_thumbnail(self, transcript_snippet: str, style: str, output_path: str) -> bool:
        context = self.generate_context_description(transcript_snippet)
        full_prompt = self.apply_style_prompt(context, style)
        full_prompt += "\n\nLeave space at top and bottom for text overlay. Vertical orientation 1280x720."
        try:
            # Try DALL-E 3
            response = openai.Image.create(
                model="dall-e-3",
                prompt=full_prompt[:1000],
                size="1792x1024",
                quality="hd",
                n=1
            )
            image_url = response.data[0].url
            img_response = requests.get(image_url)
            img = Image.open(BytesIO(img_response.content))
            img = img.resize((1280, 720), Image.Resampling.LANCZOS)
            img = self.apply_style_postprocess(img, style)
            img.save(output_path, "JPEG", quality=95)
            web_path = output_path.replace('.jpg', '_web.jpg')
            web_img = img.resize((640, 360), Image.Resampling.LANCZOS)
            web_img.save(web_path, "JPEG", quality=85)
            return True
        except Exception as e:
            print(f"DALL-E failed: {e}")
            try:
                # Fallback to Replicate (Stable Diffusion)
                import replicate
                output = replicate.run(
                    "stability-ai/stable-diffusion:db21e45d3f7023abc2a46ee38a23973f6dce16bb082a930b0c49861f96d1e5bf",
                    input={"prompt": full_prompt, "width": 1280, "height": 720, "num_outputs": 1}
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
        if style == "watercolor":
            img = img.filter(ImageFilter.SMOOTH_MORE)
        elif style == "retro_print":
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(0.8)
        elif style == "cinematic":
            draw = ImageDraw.Draw(img)
            draw.rectangle([(0,0), (1280,60)], fill="black")
            draw.rectangle([(0,660), (1280,720)], fill="black")
        elif style == "clickbait":
            from PIL import ImageEnhance
            contrast = ImageEnhance.Contrast(img)
            img = contrast.enhance(1.2)
            color = ImageEnhance.Color(img)
            img = color.enhance(1.3)
        return img
    
    def add_text_overlay(self, thumbnail_path: str, title: str, output_path: str = None):
        try:
            img = Image.open(thumbnail_path)
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype("Arial Bold.ttf", 60)
                small_font = ImageFont.truetype("Arial.ttf", 30)
            except:
                font = ImageFont.load_default()
                small_font = font
            overlay = Image.new('RGBA', img.size, (0,0,0,0))
            overlay_draw = ImageDraw.Draw(overlay)
            overlay_draw.rectangle([(0,520), (1280,720)], fill=(0,0,0,180))
            img = Image.alpha_composite(img.convert('RGBA'), overlay)
            draw = ImageDraw.Draw(img)
            words = title.split()
            line1 = " ".join(words[:4])
            line2 = " ".join(words[4:8]) if len(words) > 4 else ""
            text_color = (255,255,255)
            stroke_color = (0,0,0)
            for offset in [(2,2), (-2,-2), (2,-2), (-2,2), (0,0)]:
                x_offset, y_offset = offset
                draw_color = text_color if offset == (0,0) else stroke_color
                draw.text((100 + x_offset, 560 + y_offset), line1, font=font, fill=draw_color)
                if line2:
                    draw.text((100 + x_offset, 630 + y_offset), line2, font=small_font, fill=draw_color)
            if output_path:
                img.save(output_path, "JPEG", quality=95)
            else:
                img.save(thumbnail_path, "JPEG", quality=95)
            return True
        except Exception as e:
            print(f"Text overlay failed: {e}")
            return False
