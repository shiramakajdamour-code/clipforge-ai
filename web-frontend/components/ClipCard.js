import { useState } from 'react';
import SocialShare from './SocialShare';

export default function ClipCard({ clip, videoId }) {
  const [showVideo, setShowVideo] = useState(false);
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  return (
    <div style={{ border: '1px solid #ccc', padding: 8 }}>
      <img src={`${API_URL}/${clip.thumbnail?.web_path}`} alt="thumbnail" style={{ width: '100%' }} />
      <h4>{clip.best_title || `Clip ${clip.id}`}</h4>
      <p>Score: {clip.ai_score}</p>
      <button onClick={() => setShowVideo(true)}>Preview</button>
      {showVideo && (
        <div style={{ position: 'fixed', top: 0, left: 0, background: 'rgba(0,0,0,0.8)', padding: 20 }}>
          <video src={`${API_URL}/${clip.video_file?.web_path}`} controls autoPlay style={{ width: '100%' }} />
          <button onClick={() => setShowVideo(false)}>Close</button>
        </div>
      )}
      <SocialShare clip={clip} videoId={videoId} />
    </div>
  );
}
