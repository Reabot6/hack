import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { uploadFile, generatePackage } from '../lib/api'

const STEPS = ['upload', 'transcribing', 'researching', 'generating', 'done']

const s = {
  page: { maxWidth: 760, margin: '0 auto', padding: '48px 24px' },
  logo: { fontSize: 22, fontWeight: 700, color: '#fff', marginBottom: 48, display: 'block' },
  tagline: { fontSize: 13, color: '#666', fontWeight: 400, marginLeft: 8 },
  h1: { fontSize: 32, fontWeight: 700, marginBottom: 12, color: '#fff' },
  sub: { color: '#888', fontSize: 15, marginBottom: 40, lineHeight: 1.6 },
  dropzone: (drag) => ({
    border: `2px dashed ${drag ? '#7c6cfc' : '#333'}`,
    borderRadius: 16,
    padding: '60px 40px',
    textAlign: 'center',
    cursor: 'pointer',
    transition: 'all 0.2s',
    background: drag ? '#1a1730' : '#111',
    marginBottom: 32,
  }),
  dropIcon: { fontSize: 40, marginBottom: 16 },
  dropTitle: { fontSize: 18, fontWeight: 600, color: '#fff', marginBottom: 8 },
  dropSub: { color: '#666', fontSize: 13 },
  fileInfo: { background: '#1a1a1a', borderRadius: 12, padding: 20, marginBottom: 24, display: 'flex', alignItems: 'center', gap: 16 },
  fileIcon: { fontSize: 28 },
  fileName: { fontWeight: 600, color: '#fff', fontSize: 15 },
  fileSize: { color: '#666', fontSize: 13, marginTop: 2 },
  btn: (disabled) => ({
    background: disabled ? '#333' : 'linear-gradient(135deg, #7c6cfc, #5b4de8)',
    color: disabled ? '#666' : '#fff',
    border: 'none',
    borderRadius: 10,
    padding: '14px 32px',
    fontSize: 15,
    fontWeight: 600,
    cursor: disabled ? 'not-allowed' : 'pointer',
    width: '100%',
    transition: 'all 0.2s',
  }),
  progress: { marginTop: 32 },
  stepRow: (active, done) => ({
    display: 'flex', alignItems: 'center', gap: 12,
    padding: '12px 0', opacity: done ? 1 : active ? 1 : 0.3,
  }),
  dot: (active, done) => ({
    width: 10, height: 10, borderRadius: '50%',
    background: done ? '#4ade80' : active ? '#7c6cfc' : '#333',
    flexShrink: 0,
    boxShadow: active ? '0 0 10px #7c6cfc' : 'none',
    transition: 'all 0.4s',
  }),
  stepLabel: (active) => ({ fontSize: 14, color: active ? '#fff' : '#666', fontWeight: active ? 600 : 400 }),
  spinner: {
    width: 14, height: 14, border: '2px solid #333',
    borderTop: '2px solid #7c6cfc', borderRadius: '50%',
    animation: 'spin 0.8s linear infinite',
  },
  transcript: { marginTop: 32, background: '#111', borderRadius: 12, padding: 20 },
  tLabel: { fontSize: 12, color: '#666', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 },
  tText: { color: '#aaa', fontSize: 14, lineHeight: 1.7, fontStyle: 'italic' },
  error: { background: '#1a0808', border: '1px solid #5a1515', borderRadius: 10, padding: 16, color: '#ff6b6b', fontSize: 14, marginTop: 16 },
}

const STEP_LABELS = {
  upload: 'Uploading file...',
  transcribing: 'Transcribing audio with Whisper...',
  researching: 'Researching your niche on YouTube...',
  generating: 'Generating your upload package...',
  done: 'Done! Package ready.',
}

export default function Upload() {
  const [drag, setDrag] = useState(false)
  const [file, setFile] = useState(null)
  const [step, setStep] = useState(null)
  const [error, setError] = useState(null)
  const [transcript, setTranscript] = useState('')
  const inputRef = useRef()
  const navigate = useNavigate()

  const handleFile = (f) => {
    const allowed = ['video/mp4', 'video/quicktime', 'audio/mpeg', 'audio/wav', 'audio/mp4', 'audio/x-m4a', 'video/x-msvideo']
    const ext = f.name.split('.').pop().toLowerCase()
    const allowedExt = ['mp4', 'mov', 'mp3', 'wav', 'm4a', 'aac']
    if (!allowedExt.includes(ext)) {
      setError(`Unsupported file type. Upload MP4, MOV, MP3, WAV, or M4A.`)
      return
    }
    setFile(f)
    setError(null)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDrag(false)
    const f = e.dataTransfer.files[0]
    if (f) handleFile(f)
  }

  const handleStart = async () => {
    if (!file) return
    setError(null)
    setStep('upload')

    try {
      const fd = new FormData()
      fd.append('file', file)
      const uploadRes = await uploadFile(fd)
      const videoId = uploadRes.video_id
      setTranscript(uploadRes.transcript_preview || '')
      setStep('researching')

      const genRes = await generatePackage(videoId)
      setStep('done')

      setTimeout(() => navigate(`/dashboard/${videoId}`), 800)
    } catch (err) {
      setError(err.message)
      setStep(null)
    }
  }

  const formatSize = (bytes) => {
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const stepKeys = ['upload', 'researching', 'generating', 'done']
  const currentIdx = step ? stepKeys.indexOf(step) : -1

  return (
    <div style={s.page}>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>

      <span style={s.logo}>
        CreatorOS
        <span style={s.tagline}>while you sleep, we handle the busywork</span>
      </span>

      <h1 style={s.h1}>Upload your video</h1>
      <p style={s.sub}>
        Drop your MP4 or audio file. We'll transcribe it, research what's working
        in your niche, and generate everything you need to upload — title, description,
        tags, chapters, and captions.
      </p>

      {!step && (
        <>
          <div
            style={s.dropzone(drag)}
            onDragOver={(e) => { e.preventDefault(); setDrag(true) }}
            onDragLeave={() => setDrag(false)}
            onDrop={handleDrop}
            onClick={() => inputRef.current.click()}
          >
            <div style={s.dropIcon}>🎬</div>
            <div style={s.dropTitle}>Drop your video or audio here</div>
            <div style={s.dropSub}>MP4, MOV, MP3, WAV, M4A · Max 500MB</div>
            <input
              ref={inputRef}
              type="file"
              accept=".mp4,.mov,.mp3,.wav,.m4a,.aac"
              style={{ display: 'none' }}
              onChange={(e) => e.target.files[0] && handleFile(e.target.files[0])}
            />
          </div>

          {file && (
            <div style={s.fileInfo}>
              <span style={s.fileIcon}>📁</span>
              <div>
                <div style={s.fileName}>{file.name}</div>
                <div style={s.fileSize}>{formatSize(file.size)}</div>
              </div>
            </div>
          )}

          <button style={s.btn(!file)} disabled={!file} onClick={handleStart}>
            {file ? 'Start — Transcribe + Generate Package' : 'Select a file first'}
          </button>

          {error && <div style={s.error}>⚠️ {error}</div>}
        </>
      )}

      {step && (
        <div style={s.progress}>
          {stepKeys.map((k, i) => {
            const done = i < currentIdx
            const active = i === currentIdx
            return (
              <div key={k} style={s.stepRow(active, done)}>
                {active
                  ? <div style={s.spinner} />
                  : <div style={s.dot(active, done)} />
                }
                <span style={s.stepLabel(active || done)}>
                  {done ? '✓ ' : ''}{STEP_LABELS[k]}
                </span>
              </div>
            )
          })}

          {transcript && (
            <div style={s.transcript}>
              <div style={s.tLabel}>Transcript preview</div>
              <div style={s.tText}>"{transcript}"</div>
            </div>
          )}

          {error && <div style={s.error}>⚠️ {error}</div>}
        </div>
      )}
    </div>
  )
}
