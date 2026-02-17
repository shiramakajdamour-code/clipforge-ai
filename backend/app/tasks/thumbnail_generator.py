import cv2
import os
import numpy as np
from PIL import Image

class ThumbnailGenerator:
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
    
    def extract_frames(self, video_path, num_frames=10):
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frames = []
        for i in range(num_frames):
            frame_pos = int((i / num_frames) * total_frames)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
            ret, frame = cap.read()
            if ret:
                frames.append({
                    'frame': frame,
                    'position': frame_pos,
                    'time': frame_pos / cap.get(cv2.CAP_PROP_FPS)
                })
        cap.release()
        return frames
    
    def detect_faces(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(30,30)
        )
        return faces
    
    def score_frame(self, frame):
        score = 0
        h, w = frame.shape[:2]
        faces = self.detect_faces(frame)
        if len(faces) > 0:
            score += 50
            for (x,y,fw,fh) in faces:
                face_size = (fw*fh)/(w*h)
                score += face_size * 30
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
        score += min(sharpness/10, 20)
        mean_brightness = np.mean(gray)
        if 50 < mean_brightness < 200:
            score += 10
        return score
    
    def generate_thumbnail(self, video_path, output_path, target_time=None):
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        best_frame = None
        best_score = -1
        best_position = 0
        if target_time:
            target_frame = int(target_time * fps)
            search_range = int(fps * 5)
            start_frame = max(0, target_frame - search_range)
            end_frame = min(total_frames, target_frame + search_range)
            for frame_pos in range(start_frame, end_frame, int(fps/2)):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
                ret, frame = cap.read()
                if ret:
                    score = self.score_frame(frame)
                    if score > best_score:
                        best_score = score
                        best_frame = frame.copy()
                        best_position = frame_pos
        else:
            frames = self.extract_frames(video_path, num_frames=20)
            for fd in frames:
                score = self.score_frame(fd['frame'])
                if score > best_score:
                    best_score = score
                    best_frame = fd['frame'].copy()
                    best_position = fd['position']
        cap.release()
        if best_frame is not None:
            best_frame = self.enhance_thumbnail(best_frame)
            cv2.imwrite(output_path, best_frame)
            self.create_web_thumbnail(best_frame, output_path.replace('.jpg', '_web.jpg'))
            return {
                'path': output_path,
                'position': best_position,
                'time': best_position / fps if fps>0 else 0,
                'score': best_score,
                'has_faces': best_score > 50
            }
        return None
    
    def enhance_thumbnail(self, frame):
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        l = clahe.apply(l)
        enhanced = cv2.merge([l,a,b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        return enhanced
    
    def create_web_thumbnail(self, frame, output_path, size=(640,360)):
        resized = cv2.resize(frame, size)
        cv2.imwrite(output_path, resized, [cv2.IMWRITE_JPEG_QUALITY, 85])
    
    def generate_clip_thumbnails(self, video_path, clips, output_dir):
        os.makedirs(output_dir, exist_ok=True)
        thumbnails = []
        for i, clip in enumerate(clips):
            target_time = (clip['start'] + clip['end']) / 2
            thumb_path = os.path.join(output_dir, f"thumb_clip_{i+1}.jpg")
            result = self.generate_thumbnail(video_path, thumb_path, target_time=target_time)
            if result:
                thumbnails.append({
                    'clip_id': i+1,
                    'path': result['path'],
                    'web_path': result['path'].replace('.jpg','_web.jpg'),
                    'time': result['time'],
                    'has_faces': result['has_faces']
                })
        return thumbnails
