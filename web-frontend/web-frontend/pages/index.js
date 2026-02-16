import { useState } from 'react';
import Head from 'next/head';
import Uploader from '../components/Uploader';
import ClipGrid from '../components/ClipGrid';
import { Sparkles, Video, Image, Captions, Mic } from 'lucide-react';

export default function Home() {
  const [processedVideo, setProcessedVideo] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);

  return (
    <>
      <Head>
        <title>ClipForge - AI Video Clipping Tool</title>
        <meta name="description" content="Turn long videos into engaging short clips with AI voiceovers and smart thumbnails" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
        {/* Header */}
        <header className="bg-white shadow-sm border-b sticky top-0 z-10">
          <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="bg-primary-100 p-2 rounded-lg">
                  <Sparkles className="w-6 h-6 text-primary-600" />
                </div>
                <div>
                  <h1 className="text-xl sm:text-2xl font-bold text-gray-900">ClipForge</h1>
                  <p className="text-xs sm:text-sm text-gray-500">AI-Powered Video Clipping</p>
                </div>
              </div>
              
              {processedVideo && (
                <div className="hidden sm:flex items-center space-x-3">
                  <span className="bg-green-100 text-green-700 px-3 py-1 rounded-full text-sm font-medium">
                    {processedVideo.total_clips} clips
                  </span>
                  <span className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-sm font-medium">
                    {Math.round(processedVideo.stats?.avg_score || 0)} avg score
                  </span>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Main content */}
        <main className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
          {/* Feature badges */}
          <div className="flex flex-wrap gap-3 mb-8 justify-center">
            <div className="bg-white px-4 py-2 rounded-full shadow-sm flex items-center border">
              <Video className="w-4 h-4 text-primary-500 mr-2" />
              <span className="text-sm font-medium">60-sec clips</span>
            </div>
            <div className="bg-white px-4 py-2 rounded-full shadow-sm flex items-center border">
              <Image className="w-4 h-4 text-primary-500 mr-2" />
              <span className="text-sm font-medium">AI thumbnails</span>
            </div>
            <div className="bg-white px-4 py-2 rounded-full shadow-sm flex items-center border">
              <Captions className="w-4 h-4 text-primary-500 mr-2" />
              <span className="text-sm font-medium">Auto-captions</span>
            </div>
            <div className="bg-white px-4 py-2 rounded-full shadow-sm flex items-center border">
              <Mic className="w-4 h-4 text-primary-500 mr-2" />
              <span className="text-sm font-medium">AI voiceovers</span>
            </div>
          </div>

          {/* Uploader section */}
          <div className="mb-12">
            <Uploader 
              onUploadStart={() => setIsProcessing(true)}
              onUploadSuccess={(data) => {
                setProcessedVideo(data);
                setIsProcessing(false);
              }}
              onUploadError={() => setIsProcessing(false)}
            />
          </div>

          {/* Processing indicator */}
          {isProcessing && (
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-primary-500 border-t-transparent"></div>
              <p className="mt-2 text-gray-600">Processing video... This may take a few minutes.</p>
            </div>
          )}

          {/* Results section */}
          {processedVideo && !isProcessing && (
            <div className="space-y-8">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-semibold text-gray-900">Your AI-Generated Clips</h2>
                <span className="text-sm text-gray-500">Sorted by AI score (highest first)</span>
              </div>
              
              <ClipGrid clips={processedVideo.clips} videoId={processedVideo.video_id} />
              
              {/* Captions download */}
              {processedVideo.captions_file && (
                <div className="mt-8 p-6 bg-white rounded-xl border border-gray-200">
                  <div className="flex items-center justify-between flex-wrap gap-4">
                    <div className="flex items-center">
                      <Captions className="w-6 h-6 text-primary-500 mr-3" />
                      <div>
                        <h3 className="font-medium text-gray-900">Captions</h3>
                        <p className="text-sm text-gray-500">Download SRT file for all clips</p>
                      </div>
                    </div>
                    <a
                      href={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/${processedVideo.captions_file}`}
                      download
                      className="btn-outline inline-flex items-center"
                    >
                      <Captions className="w-4 h-4 mr-2" />
                      Download SRT
                    </a>
                  </div>
                </div>
              )}
            </div>
          )}
        </main>

        {/* Footer */}
        <footer className="bg-white border-t mt-16">
          <div className="max-w-7xl mx-auto px-4 py-6 text-center text-gray-500 text-sm">
            ClipForge - Open source AI video clipping tool
          </div>
        </footer>
      </div>
    </>
  );
    }
