// web-frontend/components/SocialShare.js
import { useState } from 'react';
import { 
  Youtube, 
  Music2, 
  Instagram, 
  Facebook, 
  Share2,
  CheckCircle,
  AlertCircle,
  Loader 
} from 'lucide-react';

export default function SocialShare({ clip, videoId }) {
  const [sharing, setSharing] = useState(false);
  const [sharedTo, setSharedTo] = useState([]);
  const [results, setResults] = useState({});
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const platforms = [
    { id: 'youtube', name: 'YouTube', icon: Youtube, color: 'bg-red-600 hover:bg-red-700' },
    { id: 'tiktok', name: 'TikTok', icon: Music2, color: 'bg-black hover:bg-gray-900' },
    { id: 'instagram', name: 'Instagram', icon: Instagram, color: 'bg-purple-600 hover:bg-purple-700' },
    { id: 'facebook', name: 'Facebook', icon: Facebook, color: 'bg-blue-600 hover:bg-blue-700' },
  ];

  const handleShare = async (platformId) => {
    setSharing(true);
    try {
      const response = await fetch(`${API_URL}/social/post/${platformId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          video_path: clip.video_file.path,
          title: clip.best_title || `Clip ${clip.id}`,
          description: clip.description || clip.text_snippet,
          user_id: 'default'
        })
      });
      const data = await response.json();
      setResults(prev => ({ ...prev, [platformId]: data }));
      if (data.success) {
        setSharedTo(prev => [...prev, platformId]);
      }
    } catch (error) {
      setResults(prev => ({ ...prev, [platformId]: { success: false, error: error.message } }));
    } finally {
      setSharing(false);
    }
  };

  const handleAuth = async (platformId) => {
    try {
      const response = await fetch(`${API_URL}/social/auth/${platformId}?user_id=default`);
      const data = await response.json();
      if (data.auth_url) {
        window.location.href = data.auth_url; // Redirect for OAuth
      }
    } catch (error) {
      console.error('Auth failed', error);
    }
  };

  return (
    <div className="mt-4 border-t pt-4">
      <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center">
        <Share2 className="w-4 h-4 mr-2" />
        Share to Social Media
      </h4>
      
      <div className="grid grid-cols-2 gap-2">
        {platforms.map((platform) => (
          <div key={platform.id}>
            <button
              onClick={() => sharedTo.includes(platform.id) ? null : handleShare(platform.id)}
              disabled={sharing || sharedTo.includes(platform.id)}
              className={`
                ${platform.color} 
                text-white px-3 py-2 rounded-lg text-sm 
                flex items-center justify-center gap-2
                transition-colors w-full
                ${(sharing || sharedTo.includes(platform.id)) ? 'opacity-50 cursor-not-allowed' : ''}
              `}
            >
              <platform.icon className="w-4 h-4" />
              {platform.name}
              {sharedTo.includes(platform.id) && <CheckCircle className="w-4 h-4 ml-1" />}
            </button>
            
            {/* If not authenticated, show auth link */}
            {results[platform.id] && results[platform.id].error?.includes('Not authenticated') && (
              <div className="mt-2 text-xs p-2 bg-yellow-50 text-yellow-700 rounded flex items-center justify-between">
                <span>Not connected</span>
                <button onClick={() => handleAuth(platform.id)} className="underline">Connect</button>
              </div>
            )}
            
            {results[platform.id] && results[platform.id].success && (
              <div className="mt-2 text-xs p-2 bg-green-50 text-green-700 rounded flex items-center">
                <CheckCircle className="w-3 h-3 mr-1" />
                Posted! {results[platform.id].url && (
                  <a href={results[platform.id].url} target="_blank" rel="noopener noreferrer" className="underline ml-1">
                    View
                  </a>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
      
      <p className="text-xs text-gray-500 mt-3">
        First-time sharing requires OAuth authorization. You'll be redirected to the platform to log in.
      </p>
    </div>
  );
}
