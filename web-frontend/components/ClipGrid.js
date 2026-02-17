import ClipCard from './ClipCard';

export default function ClipGrid({ clips, videoId }) {
  if (!clips || clips.length === 0) return <p>No clips yet.</p>;
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 16 }}>
      {clips.map(clip => <ClipCard key={clip.id} clip={clip} videoId={videoId} />)}
    </div>
  );
}
