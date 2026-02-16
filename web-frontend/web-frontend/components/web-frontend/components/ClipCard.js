import { useState } from 'react';
import { Play, Download, Star, Clock, Calendar, Mic, Image, Film } from 'lucide-react';
import Image from 'next/image';

export default function ClipCard({ clip, videoId }) {
  const [showVideo, setShowVideo] = useState(false);
  const [selectedThumbnail, setSelectedThumbnail] = useState(clip.thumbnail?.web_path || null);
  const [selectedVoiceover, setSelectedVoiceover] = useState(null);
  const [selectedLength, setSelectedLength] = useState('standard');
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Get the video file URL based on selected length
  const getVideoUrl = () => {
    if (selectedLength === 'teaser' && clip.multi_length?.teaser) {
      return `${API_URL}/${clip.multi_length.teaser.path}`;
    } else if (selectedLength === 'explainer' && clip.multi_length?.explainer) {
      return `${API_URL}/${clip.multi_length.explainer.path}`;
    } else {
      return `${API_URL}/${clip.video_file.web_path}`; // default standard
    }
  };

  // Get thumbnail URL (styled or default)
  const getThumbnailUrl = () => {
    if (selectedThumbnail) {
      return `${API_URL}/${selectedThumbnail}`;
    }
    return `${API_URL}/${clip.thumbnail?.web_path || ''}`;
  };

  return (
    <div className="card group relative">
      {/* AI Score Badge */}
      <div className="absolute top-2 right-2 z-10 flex items-center bg-yellow-100 text-yellow-700 px-2 py-1 rounded-full text-xs font-medium">
        <Star className="w-3 h-3 fill-current mr-1" />
        {clip.ai_score}
      </div>

      {/* Thumbnail with play overlay */}
      <div className="relative aspect-video mb-3 overflow-hidden rounded-lg bg-gray-100">
        {getThumbnailUrl() ? (
          <img
            src={getThumbnailUrl()}
            alt={`Clip ${clip.id}`}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gray-200">
            <Film className="w-8 h-8 text-gray-400" />
          </div>
        )}
        <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-30 transition-all flex items-center justify-center">
          <button
            onClick={() => setShowVideo(true)}
            className="bg-white rounded-full p-3 opacity-0 group-hover:opacity-100 transform scale-90 group-hover:scale-100 transition-all shadow-lg"
          >
            <Play className="w-6 h-6 text-primary-600 fill-current" />
          </button>
        </div>
        
        {/* Face detection badge */}
        {clip.thumbnail?.has_faces && (
          <span className="absolute bottom-2 left-2 bg-green-500 text-white text-xs px-2 py-1 rounded-full">
            👤 Face detected
          </span>
        )}
      </div>

      {/* Clip info */}
      <div>
        <h3 className="font-semibold text-gray-900 mb-1 line-clamp-1">
          {clip.best_title || `Clip ${clip.id}`}
        </h3>

        {/* AI Titles dropdown (optional) */}
        {clip.titles && clip.titles.length > 0 && (
          <div className="mb-2">
            <select 
              className="text-xs w-full p-1 border rounded bg-gray-50"
              onChange={(e) => {
                // In a real app, you might update the displayed title
                console.log('Selected title:', e.target.value);
              }}
            >
              {clip.titles.map((t, idx) => (
                <option key={idx} value={t.title}>
                  {t.title} (🔥{t.predicted_ctr}%)
                </option>
              ))}
            </select>
          </div>
        )}

        <p className="text-sm text-gray-600 line-clamp-2 mb-2">
          {clip.text_snippet}
        </p>

        <div className="flex items-center text-xs text-gray-500 mb-3">
          <Clock className="w-3 h-3 mr-1" />
          {formatTime(clip.duration)}
          <Calendar className="w-3 h-3 ml-3 mr-1" />
          {formatTime(clip.start_time)} - {formatTime(clip.end_time)}
        </div>

        {/* Clip Length Selector */}
        {clip.multi_length && Object.keys(clip.multi_length).length > 0 && (
          <div className="mb-3">
            <label className="text-xs text-gray-500 mb-1 block">Length</label>
            <div className="flex gap-1">
              {clip.multi_length.teaser && (
                <button
                  onClick={() => setSelectedLength('teaser')}
                  className={`flex-1 text-xs py-1 px-2 rounded ${
                    selectedLength === 'teaser' 
                      ? 'bg-primary-500 text-white' 
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  Teaser (15s)
                </button>
              )}
              <button
                onClick={() => setSelectedLength('standard')}
                className={`flex-1 text-xs py-1 px-2 rounded ${
                  selectedLength === 'standard' 
                    ? 'bg-primary-500 text-white' 
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Standard (60s)
              </button>
              {clip.multi_length.explainer && (
                <button
                  onClick={() => setSelectedLength('explainer')}
                  className={`flex-1 text-xs py-1 px-2 rounded ${
                    selectedLength === 'explainer' 
                      ? 'bg-primary-500 text-white' 
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  Explainer
                </button>
              )}
            </div>
          </div>
        )}

        {/* Thumbnail Style Selector */}
        {clip.styled_thumbnails && clip.styled_thumbnails.length > 0 && (
          <div className="mb-3">
            <label className="text-xs text-gray-500 mb-1 block flex items-center">
              <Image className="w-3 h-3 mr-1" /> Thumbnail Style
            </label>
            <div className="flex flex-wrap gap-1">
              {clip.styled_thumbnails.map((thumb) => (
                <button
                  key={thumb.style}
                  onClick={() => setSelectedThumbnail(thumb.web_path)}
                  className={`text-xs px-2 py-1 rounded ${
                    selectedThumbnail === thumb.web_path
                      ? 'bg-primary-500 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {thumb.style}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Voiceover Selector */}
        {clip.voiceover_options && clip.voiceover_options.length > 0 && (
          <div className="mb-3">
            <label className="text-xs text-gray-500 mb-1 block flex items-center">
              <Mic className="w-3 h-3 mr-1" /> Voiceover
            </label>
            <div className="flex flex-wrap gap-1">
              {clip.voiceover_options.map((vo) => (
                <button
                  key={vo.style}
                  onClick={() => setSelectedVoiceover(vo.audio_path)}
                  className={`text-xs px-2 py-1 rounded ${
                    selectedVoiceover === vo.audio_path
                      ? 'bg-purple-500 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {vo.style === 'dual_host' && '🎙️ Dual'}
                  {vo.style === 'interview' && '🎤 Interview'}
                  {vo.style === 'debate' && '⚖️ Debate'}
                  {vo.style === 'storytelling' && '📖 Story'}
                  {vo.style === 'solo' && '🎧 Solo'}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Description (collapsible) */}
        {clip.description && (
          <details className="mb-3 text-xs">
            <summary className="text-gray-500 cursor-pointer">Description</summary>
            <p className="mt-1 text-gray-600">{clip.description}</p>
          </details>
        )}

        {/* Hashtags */}
        {clip.hashtags && clip.hashtags.length > 0 && (
          <div className="mb-3 flex flex-wrap gap-1">
            {clip.hashtags.slice(0, 3).map((tag, idx) => (
              <span key={idx} className="text-xs bg-blue-50 text-blue-600 px-2 py-1 rounded">
                {tag}
              </span>
            ))}
            {clip.hashtags.length > 3 && (
              <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                +{clip.hashtags.length - 3}
              </span>
            )}
          </div>
        )}

        {/* Action buttons */}
        <div className="flex gap-2 mt-3">
          <button
            onClick={() => setShowVideo(true)}
            className="flex-1 bg-primary-500 text-white px-3 py-2 rounded-lg text-sm hover:bg-primary-600 transition-colors flex items-center justify-center"
          >
            <Play className="w-4 h-4 mr-1" /> Preview
          </button>
          <a
            href={getVideoUrl()}
            download
            className="flex-1 bg-gray-100 text-gray-700 px-3 py-2 rounded-lg text-sm hover:bg-gray-200 transition-colors flex items-center justify-center"
          >
            <Download className="w-4 h-4 mr-1" /> Download
          </a>
        </div>
      </div>

      {/* Video preview modal */}
      {showVideo && (
        <div className="fixed inset-0 bg-black bg-opacity-75 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-4xl w-full">
            <div className="p-4 border-b flex justify-between items-center">
              <h3 className="font-semibold text-gray-900">
                {clip.best_title || `Clip ${clip.id}`}
              </h3>
              <button
                onClick={() => setShowVideo(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            <video
              src={getVideoUrl()}
              controls
              autoPlay
              className="w-full aspect-video"
            />
          </div>
        </div>
      )}
    </div>
  );
    }
