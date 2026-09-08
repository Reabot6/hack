import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { listVideos } from '../lib/api'

const s = {
  page: { maxWidth: 900, margin: '0 auto', padding: '48px 24px' },
  nav: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 48 },
  logo: { fontSize: 22, fontWeight: 700, color: '#fff' },
  tagline: { fontSize: 13, color: '#555', marginTop: 2 },
  uploadBtn: {
    background: 'linear-gradient(135deg, #7c6cfc, #5b4de8)',
    color: '#fff', border: 'none', borderRadius: 10,
    padding: '12px 24px', fontSize: 14, fontWeight: 600, cursor: 'pointer',
  },
  hero: { marginBottom: 48 },
  h1: { fontSize: 36, fontWeight: 700, color: '#fff', marginBottom: 12, lineHeight: 1.2 },
  sub: { color: '#666', fontSize: 16, lineHeight: 1.6, maxWidth: 560 },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 },
  card: { background: '#111', borderRadius: 14, padding: 24, cursor: 'pointer', border: '1px solid #1a1a1a', transition: 'border-color 0.2s' },
  cardTitle: { fontSize: 16, fontWeight: 600, color: '#fff', marginBottom: 8, lineHeight: 1.4 },
  cardMeta: { fontSize: 12, color: '#555' },
  badge: (status) => ({
    display: 'inline-block', fontSize: 11, fontWeight: 600,
    padding: '3px 9px', borderRadius: 20, marginBottom: 12,
    background: status === 'packaged' ? '#0d2e0d' : '#1a1a2e',
    color: status === 'packaged' ? '#4ade80' : '#7c6cfc',
  }),
  empty: { textAlign: 'center', padding: '80px 24px', color: '#444' },
  emptyIcon: { fontSize: 48, marginBottom: 16 },
  emptyTitle: { fontSize: 20, fontWeight: 600, color: '#666', marginBottom: 8 },
  emptySub: { fontSize: 14, color: '#444', lineHeight: 1.6 },
}

const STATUS_LABEL = {
  uploading: 'Uploading',
  extracting_audio: 'Extracting audio',
  transcribing: 'Transcribing',
  researching: 'Researching',
  generating: 'Generating',
  packaged: 'Ready',
  failed: 'Failed',
}

export default function Videos() {
  const [videos, setVideos] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    listVideos()
      .then(res => setVideos(res.videos || []))
      .catch(() => setVideos([]))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div style={s.page}>
      <nav style={s.nav}>
        <div>
          <div style={s.logo}>CreatorOS</div>
          <div style={s.tagline}>while you sleep, we handle the busywork</div>
        </div>
        <button style={s.uploadBtn} onClick={() => navigate('/upload')}>+ Upload video</button>
      </nav>

      <div style={s.hero}>
        <h1 style={s.h1}>Your videos</h1>
        <p style={s.sub}>
          Upload a video, get a complete upload package. Then come back to find
          clip opportunities waiting, comment replies drafted, and alerts fired.
        </p>
      </div>

      {loading && <div style={{ color: '#444', fontSize: 14 }}>Loading...</div>}

      {!loading && videos.length === 0 && (
        <div style={s.empty}>
          <div style={s.emptyIcon}>🎬</div>
          <div style={s.emptyTitle}>No videos yet</div>
          <div style={s.emptySub}>
            Upload your first video to get started.<br />
            We'll handle the title, description, tags, captions, and clips.
          </div>
          <button
            style={{ ...s.uploadBtn, marginTop: 24, display: 'inline-block' }}
            onClick={() => navigate('/upload')}
          >
            Upload your first video
          </button>
        </div>
      )}

      <div style={s.grid}>
        {videos.map(v => (
          <div
            key={v.id}
            style={s.card}
            onClick={() => navigate(`/dashboard/${v.id}`)}
            onMouseEnter={e => e.currentTarget.style.borderColor = '#333'}
            onMouseLeave={e => e.currentTarget.style.borderColor = '#1a1a1a'}
          >
            <div style={s.badge(v.status)}>{STATUS_LABEL[v.status] || v.status}</div>
            <div style={s.cardTitle}>{v.original_filename}</div>
            {v.topic && <div style={{ ...s.cardMeta, color: '#888', marginBottom: 6 }}>{v.topic}</div>}
            <div style={s.cardMeta}>{new Date(v.created_at).toLocaleDateString()}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
