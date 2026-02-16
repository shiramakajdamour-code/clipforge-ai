import os
import json
import secrets
import hashlib
import base64
import requests
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ==================== Base Classes ====================

@dataclass
class PlatformCredentials:
    platform: str
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[int] = None
    user_id: Optional[str] = None
    page_id: Optional[str] = None
    instagram_id: Optional[str] = None

class SocialShareBase:
    def __init__(self, credentials_dir="./credentials"):
        self.credentials_dir = Path(credentials_dir)
        self.credentials_dir.mkdir(exist_ok=True)
        
    def save_credentials(self, platform: str, user_id: str, credentials: Dict):
        cred_file = self.credentials_dir / f"{platform}_{user_id}.json"
        with open(cred_file, 'w') as f:
            json.dump(credentials, f)
        print(f"✅ Credentials saved for {platform}: {user_id}")
        
    def load_credentials(self, platform: str, user_id: str) -> Optional[Dict]:
        cred_file = self.credentials_dir / f"{platform}_{user_id}.json"
        if cred_file.exists():
            with open(cred_file, 'r') as f:
                return json.load(f)
        return None

# ==================== YouTube Sharer ====================

class YouTubeSharer(SocialShareBase):
    SCOPES = ['https://www.googleapis.com/auth/youtube.upload',
              'https://www.googleapis.com/auth/youtube.force-ssl']
    
    def __init__(self, credentials_dir="./credentials"):
        super().__init__(credentials_dir)
        self.client_secrets_file = 'client_secrets.json'  # You need to provide this
        
    def get_auth_url(self) -> str:
        flow = Flow.from_client_secrets_file(
            self.client_secrets_file,
            scopes=self.SCOPES,
            redirect_uri='http://localhost:8000/social/auth/youtube/callback'
        )
        auth_url, _ = flow.authorization_url(prompt='consent')
        return auth_url
        
    def authenticate(self, user_id: str, auth_code: Optional[str] = None):
        creds = None
        saved = self.load_credentials("youtube", user_id)
        if saved:
            creds = Credentials.from_authorized_user_info(saved, self.SCOPES)
            
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(GoogleRequest())
            elif auth_code:
                flow = Flow.from_client_secrets_file(
                    self.client_secrets_file,
                    scopes=self.SCOPES,
                    redirect_uri='http://localhost:8000/social/auth/youtube/callback'
                )
                flow.fetch_token(code=auth_code)
                creds = flow.credentials
                self.save_credentials("youtube", user_id, json.loads(creds.to_json()))
            else:
                raise ValueError("Authentication required")
                
        self.youtube = build('youtube', 'v3', credentials=creds)
        return self.youtube
        
    def upload_video(self, video_path: str, title: str, description: str = "",
                     tags: list = None, privacy_status: str = "unlisted") -> Dict:
        try:
            body = {
                'snippet': {
                    'title': title[:100],
                    'description': description[:5000],
                    'tags': tags or [],
                    'categoryId': '22'
                },
                'status': {
                    'privacyStatus': privacy_status,
                    'selfDeclaredMadeForKids': False
                }
            }
            media = MediaFileUpload(video_path, chunksize=1024*1024, resumable=True)
            request = self.youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    print(f"Upload progress: {int(status.progress() * 100)}%")
            return {
                'success': True,
                'video_id': response['id'],
                'url': f"https://youtu.be/{response['id']}",
                'platform': 'youtube'
            }
        except Exception as e:
            return {'success': False, 'error': str(e), 'platform': 'youtube'}

# ==================== TikTok Sharer ====================

class TikTokSharer(SocialShareBase):
    def __init__(self, credentials_dir="./credentials"):
        super().__init__(credentials_dir)
        self.client_key = os.getenv("TIKTOK_CLIENT_KEY")
        self.client_secret = os.getenv("TIKTOK_CLIENT_SECRET")
        self.redirect_uri = os.getenv("TIKTOK_REDIRECT_URI", "http://localhost:8000/social/auth/tiktok/callback")
        
    def get_auth_url(self) -> str:
        code_verifier = secrets.token_urlsafe(64)
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).decode().rstrip("=")
        
        # Store code_verifier temporarily
        self.save_credentials("tiktok_verifier", "current", {"code_verifier": code_verifier})
        
        auth_url = (
            f"https://www.tiktok.com/v2/auth/authorize/"
            f"?client_key={self.client_key}"
            f"&response_type=code"
            f"&scope=video.upload,video.publish,user.info.basic"
            f"&redirect_uri={self.redirect_uri}"
            f"&code_challenge={code_challenge}"
            f"&code_challenge_method=S256"
        )
        return auth_url
        
    def exchange_code(self, auth_code: str) -> Dict:
        verifier_data = self.load_credentials("tiktok_verifier", "current")
        code_verifier = verifier_data.get('code_verifier') if verifier_data else None
        
        token_url = "https://open.tiktokapis.com/v2/oauth/token/"
        data = {
            "client_key": self.client_key,
            "client_secret": self.client_secret,
            "code": auth_code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
            "code_verifier": code_verifier
        }
        resp = requests.post(token_url, data=data)
        token_data = resp.json()
        if 'access_token' in token_data:
            self.save_credentials("tiktok", token_data['open_id'], token_data)
            return {'success': True, **token_data}
        else:
            return {'success': False, 'error': token_data}
            
    def post_video(self, video_path: str, title: str, user_id: str = "default") -> Dict:
        saved = self.load_credentials("tiktok", user_id)
        if not saved:
            return {'success': False, 'error': 'Not authenticated', 'platform': 'tiktok'}
            
        access_token = saved['access_token']
        open_id = saved['open_id']
        
        # Step 1: Initialize upload
        init_url = "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/"
        headers = {
            'Authorization': f"Bearer {access_token}",
            'Content-Type': 'application/json; charset=UTF-8'
        }
        init_data = {
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": os.path.getsize(video_path),
                "chunk_size": 1024 * 1024,  # 1MB chunks
                "total_chunk_count": (os.path.getsize(video_path) + (1024*1024 - 1)) // (1024*1024)
            }
        }
        init_resp = requests.post(init_url, headers=headers, json=init_data)
        init_result = init_resp.json()
        if init_result.get('error'):
            return {'success': False, 'error': init_result['error'], 'platform': 'tiktok'}
            
        upload_url = init_result['data']['upload_url']
        
        # Step 2: Upload file in chunks (simplified: upload whole file)
        with open(video_path, 'rb') as f:
            file_content = f.read()
        upload_headers = {
            'Content-Type': 'video/mp4',
            'Content-Length': str(len(file_content))
        }
        upload_resp = requests.put(upload_url, headers=upload_headers, data=file_content)
        if upload_resp.status_code != 200:
            return {'success': False, 'error': 'Upload failed', 'platform': 'tiktok'}
            
        # Step 3: Publish
        publish_url = "https://open.tiktokapis.com/v2/post/publish/inbox/video/publish/"
        publish_data = {
            "post_info": {
                "title": title,
                "privacy_level": "PUBLIC",
                "disable_comment": False,
                "disable_duet": False,
                "disable_stitch": False,
                "video_cover_timestamp_ms": 1000
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_id": init_result['data']['video_id']
            }
        }
        publish_resp = requests.post(publish_url, headers=headers, json=publish_data)
        publish_result = publish_resp.json()
        if publish_result.get('error'):
            return {'success': False, 'error': publish_result['error'], 'platform': 'tiktok'}
            
        return {
            'success': True,
            'publish_id': publish_result['data']['publish_id'],
            'platform': 'tiktok'
        }

# ==================== Meta (Instagram/Facebook) Sharer ====================

class MetaSharer(SocialShareBase):
    def __init__(self, credentials_dir="./credentials"):
        super().__init__(credentials_dir)
        self.app_id = os.getenv("META_APP_ID")
        self.app_secret = os.getenv("META_APP_SECRET")
        self.redirect_uri = os.getenv("META_REDIRECT_URI", "http://localhost:8000/social/auth/meta/callback")
        self.graph_url = "https://graph.facebook.com/v18.0"
        
    def get_auth_url(self, platform: str) -> str:
        if platform == "instagram":
            scope = "instagram_basic,instagram_content_publish,pages_read_engagement"
        else:  # facebook
            scope = "pages_manage_posts,pages_read_engagement"
            
        auth_url = (
            f"https://www.facebook.com/v18.0/dialog/oauth"
            f"?client_id={self.app_id}"
            f"&redirect_uri={self.redirect_uri}"
            f"&scope={scope}"
        )
        return auth_url
        
    def exchange_code(self, auth_code: str) -> Dict:
        # Exchange for short-lived token
        token_resp = requests.get(f"{self.graph_url}/oauth/access_token", params={
            'client_id': self.app_id,
            'client_secret': self.app_secret,
            'redirect_uri': self.redirect_uri,
            'code': auth_code
        })
        token_data = token_resp.json()
        if 'access_token' not in token_data:
            return {'success': False, 'error': token_data}
            
        short_token = token_data['access_token']
        
        # Exchange for long-lived token
        long_resp = requests.get(f"{self.graph_url}/oauth/access_token", params={
            'grant_type': 'fb_exchange_token',
            'client_id': self.app_id,
            'client_secret': self.app_secret,
            'fb_exchange_token': short_token
        })
        long_data = long_resp.json()
        long_token = long_data['access_token']
        
        # Get pages
        pages_resp = requests.get(f"{self.graph_url}/me/accounts", params={
            'access_token': long_token
        })
        pages_data = pages_resp.json()
        if not pages_data.get('data'):
            return {'success': False, 'error': 'No Facebook pages found'}
            
        page = pages_data['data'][0]
        page_id = page['id']
        page_token = page['access_token']
        
        # Get Instagram business account
        ig_resp = requests.get(f"{self.graph_url}/{page_id}", params={
            'fields': 'instagram_business_account',
            'access_token': page_token
        })
        ig_data = ig_resp.json()
        ig_user_id = ig_data.get('instagram_business_account', {}).get('id')
        
        creds = {
            'access_token': long_token,
            'page_token': page_token,
            'page_id': page_id,
            'ig_user_id': ig_user_id
        }
        self.save_credentials("meta", page_id, creds)
        return {'success': True, **creds}
        
    def post_instagram_reel(self, video_path: str, caption: str, user_id: str = "default") -> Dict:
        saved = self.load_credentials("meta", user_id)
        if not saved:
            return {'success': False, 'error': 'Not authenticated', 'platform': 'instagram'}
            
        ig_user_id = saved['ig_user_id']
        access_token = saved['access_token']
        
        # Video must be publicly accessible. For simplicity, we assume it's hosted.
        # In production, you'd upload to a cloud storage and provide the URL.
        video_url = f"http://your-domain.com/{video_path}"  # Replace with actual public URL
        
        # Create media container
        create_url = f"{self.graph_url}/{ig_user_id}/media"
        create_params = {
            'media_type': 'REELS',
            'video_url': video_url,
            'caption': caption[:2200],
            'share_to_feed': True,
            'thumb_offset_ms': 2000,
            'access_token': access_token
        }
        create_resp = requests.post(create_url, data=create_params)
        create_data = create_resp.json()
        if 'id' not in create_data:
            return {'success': False, 'error': create_data, 'platform': 'instagram'}
            
        container_id = create_data['id']
        time.sleep(5)  # Wait for processing
        
        # Publish
        publish_url = f"{self.graph_url}/{ig_user_id}/media_publish"
        publish_params = {
            'creation_id': container_id,
            'access_token': access_token
        }
        publish_resp = requests.post(publish_url, data=publish_params)
        publish_data = publish_resp.json()
        
        return {
            'success': True,
            'media_id': publish_data.get('id'),
            'platform': 'instagram'
        }
        
    def post_facebook_video(self, video_path: str, title: str, description: str = "", user_id: str = "default") -> Dict:
        saved = self.load_credentials("meta", user_id)
        if not saved:
            return {'success': False, 'error': 'Not authenticated', 'platform': 'facebook'}
            
        page_id = saved['page_id']
        page_token = saved['page_token']
        
        # Video must be publicly accessible
        video_url = f"http://your-domain.com/{video_path}"
        
        post_url = f"{self.graph_url}/{page_id}/videos"
        post_params = {
            'file_url': video_url,
            'description': f"{title}\n\n{description}",
            'published': True,
            'access_token': page_token
        }
        post_resp = requests.post(post_url, data=post_params)
        post_data = post_resp.json()
        
        if 'id' in post_data:
            return {
                'success': True,
                'video_id': post_data['id'],
                'url': f"https://facebook.com/{post_data['id']}",
                'platform': 'facebook'
            }
        else:
            return {'success': False, 'error': post_data, 'platform': 'facebook'}

# ==================== FastAPI Router ====================

social_router = APIRouter(prefix="/social", tags=["social"])

# Initialize sharers (you may want to pass credentials dir)
youtube_sharer = YouTubeSharer()
tiktok_sharer = TikTokSharer()
meta_sharer = MetaSharer()
base = SocialShareBase()

@social_router.get("/auth/{platform}")
async def auth_platform(platform: str, user_id: str = "default"):
    """Get authorization URL for platform"""
    try:
        if platform == "youtube":
            url = youtube_sharer.get_auth_url()
        elif platform == "tiktok":
            url = tiktok_sharer.get_auth_url()
        elif platform in ["instagram", "facebook"]:
            url = meta_sharer.get_auth_url(platform)
        else:
            raise HTTPException(status_code=400, detail="Unsupported platform")
        return {"auth_url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@social_router.get("/auth/{platform}/callback")
async def auth_callback(platform: str, code: str, state: Optional[str] = None):
    """OAuth callback handler"""
    try:
        if platform == "youtube":
            # YouTube callback handled separately via flow, but we can just redirect
            return RedirectResponse(url="/social/connected?platform=youtube&success=true")
        elif platform == "tiktok":
            result = tiktok_sharer.exchange_code(code)
            if result['success']:
                return RedirectResponse(url="/social/connected?platform=tiktok&success=true")
            else:
                return RedirectResponse(url=f"/social/connected?platform=tiktok&success=false&error={result.get('error')}")
        elif platform in ["instagram", "facebook"]:
            result = meta_sharer.exchange_code(code)
            if result['success']:
                return RedirectResponse(url=f"/social/connected?platform={platform}&success=true")
            else:
                return RedirectResponse(url=f"/social/connected?platform={platform}&success=false&error={result.get('error')}")
        else:
            return RedirectResponse(url="/social/connected?success=false")
    except Exception as e:
        return RedirectResponse(url=f"/social/connected?success=false&error={str(e)}")

@social_router.post("/post/{platform}")
async def post_to_platform(platform: str, request: Request):
    data = await request.json()
    video_path = data.get("video_path")
    title = data.get("title", "")
    description = data.get("description", "")
    user_id = data.get("user_id", "default")
    
    if not video_path:
        raise HTTPException(status_code=400, detail="video_path required")
        
    if platform == "youtube":
        youtube_sharer.authenticate(user_id)
        result = youtube_sharer.upload_video(video_path, title, description)
    elif platform == "tiktok":
        result = tiktok_sharer.post_video(video_path, title, user_id)
    elif platform == "instagram":
        result = meta_sharer.post_instagram_reel(video_path, title + "\n" + description, user_id)
    elif platform == "facebook":
        result = meta_sharer.post_facebook_video(video_path, title, description, user_id)
    else:
        raise HTTPException(status_code=400, detail="Unsupported platform")
        
    return JSONResponse(content=result)

@social_router.get("/connected")
async def connected(platform: str, success: bool, error: Optional[str] = None):
    """Simple confirmation endpoint (would be a nice HTML page in production)"""
    if success:
        return {"message": f"✅ Successfully connected to {platform}!"}
    else:
        return {"message": f"❌ Failed to connect to {platform}: {error}"}
