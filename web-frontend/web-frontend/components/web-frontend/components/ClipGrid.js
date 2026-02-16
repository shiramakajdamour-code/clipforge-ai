import ClipCard from './ClipCard';

export default function ClipGrid({ clips, videoId }) {
  if (!clips || clips.length === 0) {
    return (
      <div className="text-center py-12 bg-white rounded-xl border border-gray-200">
        <p className="text-gray-500">No clips generated yet</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {clips.map((clip) => (
        <ClipCard key={clip.id} clip={clip} videoId={videoId} />
      ))}
    </div>
  );
      }
