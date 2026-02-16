import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X, CheckCircle, AlertCircle, Loader } from 'lucide-react';
import axios from 'axios';

export default function Uploader({ onUploadStart, onUploadSuccess, onUploadError }) {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [file, setFile] = useState(null);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [taskId, setTaskId] = useState(null);

  const onDrop = useCallback((acceptedFiles) => {
    const selectedFile = acceptedFiles[0];
    if (selectedFile && selectedFile.type.startsWith('video/')) {
      setFile(selectedFile);
      setError(null);
    } else {
      setError('Please select a valid video file');
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'video/*': ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v']
    },
    maxFiles: 1,
    maxSize: 500 * 1024 * 1024, // 500MB
  });

  const uploadFile = async () => {
    if (!file) return;

    setUploading(true);
    setError(null);
    setProgress(0);
    setSuccess(false);
    if (onUploadStart) onUploadStart();

    const formData = new FormData();
    formData.append('file', file);

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      
      const response = await axios.post(`${API_URL}/api/upload`, formData, {
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setProgress(percentCompleted);
        },
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const { task_id } = response.data;
      setTaskId(task_id);
      setProgress(100);
      
      // Start polling for job completion
      pollJobStatus(task_id);
      
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Upload failed. Please try again.';
      setError(errorMsg);
      setUploading(false);
      if (onUploadError) onUploadError(errorMsg);
    }
  };

  const pollJobStatus = async (taskId) => {
    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const interval = setInterval(async () => {
      try {
        const response = await axios.get(`${API_URL}/api/status/${taskId}`);
        
        if (response.data.status === 'SUCCESS') {
          clearInterval(interval);
          setUploading(false);
          setSuccess(true);
          if (onUploadSuccess) {
            onUploadSuccess(response.data.result);
          }
        } else if (response.data.status === 'FAILURE') {
          clearInterval(interval);
          setError('Processing failed. Please try again.');
          setUploading(false);
          if (onUploadError) onUploadError('Processing failed');
        } else {
          // Update progress based on stage (optional)
          const stage = response.data.result?.stage;
          if (stage) {
            // You could map stages to progress
            const stageProgress = {
              'analyzing with Whisper AI': 40,
              'generating captions': 55,
              'generating thumbnails': 70,
              'extracting video clips': 85,
              'generating AI titles': 95,
            }[stage];
            if (stageProgress) setProgress(stageProgress);
          }
        }
      } catch (err) {
        console.error('Status check failed:', err);
        // Don't clear interval on network error, just retry
      }
    }, 2000); // poll every 2 seconds
  };

  const removeFile = () => {
    setFile(null);
    setError(null);
    setSuccess(false);
    setTaskId(null);
    setProgress(0);
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      {!file ? (
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors
            ${isDragActive ? 'border-primary-500 bg-primary-50' : 'border-gray-300 hover:border-primary-400 bg-white'}`}
        >
          <input {...getInputProps()} />
          <Upload className="w-16 h-16 mx-auto mb-4 text-gray-400" />
          {isDragActive ? (
            <p className="text-lg text-primary-600 font-medium">Drop your video here...</p>
          ) : (
            <>
              <p className="text-lg mb-2 font-medium text-gray-700">Drag & drop your video here</p>
              <p className="text-sm text-gray-500">or click to browse</p>
              <p className="text-xs text-gray-400 mt-4">Supports: MP4, MOV, AVI, MKV (max 500MB)</p>
            </>
          )}
        </div>
      ) : (
        <div className="border rounded-xl p-6 bg-white shadow-sm">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center">
              <File className="w-8 h-8 text-primary-500 mr-3" />
              <div>
                <p className="font-medium text-gray-900">{file.name}</p>
                <p className="text-sm text-gray-500">
                  {formatFileSize(file.size)}
                </p>
              </div>
            </div>
            {!uploading && !success && (
              <button onClick={removeFile} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            )}
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-lg flex items-center">
              <AlertCircle className="w-5 h-5 mr-2 flex-shrink-0" />
              <span className="text-sm">{error}</span>
            </div>
          )}

          {!uploading && !success && (
            <button
              onClick={uploadFile}
              className="w-full btn-primary py-3 text-lg"
              disabled={!file}
            >
              Upload Video
            </button>
          )}

          {uploading && (
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Uploading & Processing...</span>
                <span className="font-medium text-primary-600">{progress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div
                  className="bg-primary-600 rounded-full h-2.5 transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <p className="text-xs text-gray-500 text-center">
                {progress < 30 ? 'Uploading video...' : 
                 progress < 60 ? 'Analyzing with AI...' : 
                 progress < 90 ? 'Generating clips and thumbnails...' : 
                 'Finalizing...'}
              </p>
            </div>
          )}

          {success && (
            <div className="text-center py-4">
              <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-2" />
              <p className="text-green-600 font-medium text-lg">Upload successful!</p>
              <p className="text-sm text-gray-500">Your clips are ready below.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
         }
