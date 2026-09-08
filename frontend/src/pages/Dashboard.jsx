import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  getVideo, getPackage, getAnalytics, getComments,
  approveComment, skipComment, batchApproveComments,
  getClips, detectClips, updateClip,
  getAlerts, createAlert, deleteAlert,
  getNotifications, markNotificationRead,
  linkYouTube, getYouTubeConnection, connectYouTube, publishToYouTube, publishShortToYouTube
} from '../lib/api'

const s = {
  page: { maxWidth: 1100, margin: '0 auto', padding: '32px 24px' },
  nav: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 40 },
  logo: { fontSize: 20, fontWeight: 700, color: '#fff', textDecoration: 'none' },
  back: { color: '#666', fontSize: 14, cursor: 'pointer', background: 'none', border: 'none' },
  title: { fontSize: 26, fontWeight: 700, color: '#fff', marginBottom: 4 },
  meta: { color: '#666', fontSize: 13, marginBottom: 32 },
  tabs: { display: 'flex', gap: 4, marginBottom: 32, borderBottom: '1px solid #1e1e1e', paddingBottom: 0 },
  tab: (active) => ({
    padding: '10px 20px', fontSize: 14, fontWeight: active ? 600 : 400,
    color: active ? '#fff' : '#666', cursor: 'pointer', background: 'none',
    border: 'none', borderBottom: active ? '2px solid #7c6cfc' : '2px solid transparent',
    marginBottom: -1, transition: 'all 0.15s',
  }),
  grid: { display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 16, marginBottom: 32 },
  statCard: { background: '#111', borderRadius: 12, padding: 20 },
  statNum: { fontSize: 28, fontWeight: 700, color: '#fff', marginBottom: 4 },
  statLabel: { fontSize: 12, color: '#666', textTransform: 'uppercase', letterSpacing: 0.5 },
  section: { background: '#111', borderRadius: 12, padding: 24, marginBottom: 20 },
  sectionTitle: { fontSize: 16, fontWeight: 600, color: '#fff', marginBottom: 16 },
  tag: { display: 'inline-block', background: '#1e1e2e', color: '#7c6cfc', padding: '4px 10px', borderRadius: 6, fontSize: 12, margin: '3px 3px 3px 0' },
  copyBtn: { background: '#1e1e2e', border: 'none', color: '#7c6cfc', padding: '6px 14px', borderRadius: 8, fontSize: 12, cursor: 'pointer', marginLeft: 8 },
  titleOption: { background: '#0d0d0d', border: '1px solid #1e1e1e', borderRadius: 10, padding: 16, marginBottom: 10 },
  titleText: { fontSize: 15, color: '#fff', fontWeight: 500, marginBottom: 6 },
  titleReason: { fontSize: 12, color: '#666' },
  rankBadge: { background: '#7c6cfc22', color: '#7c6cfc', fontSize: 11, padding: '2px 8px', borderRadius: 20, float: 'right' },
  textarea: { width: '100%', background: '#0d0d0d', border: '1px solid #1e1e1e', borderRadius: 10, color: '#ccc', padding: 16, fontSize: 14, lineHeight: 1.7, minHeight: 120, resize: 'vertical', fontFamily: 'inherit' },
  downloadBtn: { background: '#1e2e1e', border: 'none', color: '#4ade80', padding: '8px 16px', borderRadius: 8, fontSize: 13, cursor: 'pointer', marginTop: 10 },
  commentCard: { borderBottom: '1px solid #1a1a1a', padding: '16px 0' },
  commenterName: { fontSize: 13, fontWeight: 600, color: '#888', marginBottom: 6 },
  commentText: { fontSize: 14, color: '#ccc', marginBottom: 12, lineHeight: 1.6 },
  draftReply: { background: '#0d1a0d', border: '1px solid #1a2e1a', borderRadius: 8, padding: 12, fontSize: 13, color: '#4ade80', marginBottom: 10, lineHeight: 1.6 },
  commentActions: { display: 'flex', gap: 8 },
  approveBtn: { background: '#0d2e0d', border: '1px solid #1a4a1a', color: '#4ade80', padding: '6px 14px', borderRadius: 7, fontSize: 12, cursor: 'pointer' },
  skipBtn: { background: '#1a1a1a', border: '1px solid #2a2a2a', color: '#666', padding: '6px 14px', borderRadius: 7, fontSize: 12, cursor: 'pointer' },
  batchBtn: { background: '#0d2e0d', border: '1px solid #1a4a1a', color: '#4ade80', padding: '10px 20px', borderRadius: 9, fontSize: 14, cursor: 'pointer', marginBottom: 20, fontWeight: 600 },
  clipCard: { background: '#0d0a1e', border: '1px solid #2a2050', borderRadius: 12, padding: 20, marginBottom: 16 },
  clipBadge: { display: 'inline-block', background: '#ff4d0022', color: '#ff6b35', padding: '3px 10px', borderRadius: 20, fontSize: 12, fontWeight: 600, marginBottom: 12 },
  clipTitle: { fontSize: 16, fontWeight: 600, color: '#fff', marginBottom: 8 },
  clipWhy: { fontSize: 13, color: '#888', marginBottom: 16, lineHeight: 1.6 },
  clipMeta: { fontSize: 12, color: '#666', marginBottom: 16 },
  clipActions: { display: 'flex', gap: 8 },
  scheduleBtn: { background: '#1e1a2e', border: '1px solid #3a3060', color: '#7c6cfc', padding: '8px 16px', borderRadius: 8, fontSize: 13, cursor: 'pointer' },
  dismissBtn: { background: '#1a1a1a', border: '1px solid #2a2a2a', color: '#666', padding: '8px 16px', borderRadius: 8, fontSize: 13, cursor: 'pointer' },
  alertForm: { display: 'flex', gap: 10, marginTop: 16, flexWrap: 'wrap' },
  select: { background: '#0d0d0d', border: '1px solid #2a2a2a', color: '#ccc', padding: '8px 12px', borderRadius: 8, fontSize: 13 },
  input: { background: '#0d0d0d', border: '1px solid #2a2a2a', color: '#ccc', padding: '8px 12px', borderRadius: 8, fontSize: 13, width: 120 },
  addAlertBtn: { background: '#1e1a2e', border: '1px solid #3a3060', color: '#7c6cfc', padding: '8px 16px', borderRadius: 8, fontSize: 13, cursor: 'pointer' },
  alertRow: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 0', borderBottom: '1px solid #1a1a1a' },
  alertText: { fontSize: 14, color: '#ccc' },
  deleteBtn: { background: 'none', border: 'none', color: '#666', cursor: 'pointer', fontSize: 18 },
  notifCard: { background: '#0a1a0a', border: '1px solid #1a3a1a', borderRadius: 10, padding: 14, marginBottom: 10, display: 'flex', alignItems: 'center', justifyContent: 'space-between' },
  notifText: { fontSize: 14, color: '#ccc' },
  empty: { color: '#444', fontSize: 14, textAlign: 'center', padding: '40px 0' },
  linkYtInput: { background: '#0d0d0d', border: '1px solid #2a2a2a', color: '#ccc', padding: '8px 12px', borderRadius: 8, fontSize: 13, width: 260 },
  linkYtBtn: { background: '#1e1a2e', border: '1px solid #3a3060', color: '#7c6cfc', padding: '8px 16px', borderRadius: 8, fontSize: 13, cursor: 'pointer', marginLeft: 8 },
}

function copy(text) { navigator.clipboard.writeText(text) }

function downloadSrt(content, filename = 'captions.srt') {
  const blob = new Blob([content], { type: 'text/plain' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = filename
  a.click()
}

export default function Dashboard() {
  const { videoId } = useParams()
  const navigate = useNavigate()
  const [tab, setTab] = useState('package')
  const [video, setVideo] = useState(null)
  const [pkg, setPkg] = useState(null)
  const [analytics, setAnalytics] = useState(null)
  const [comments, setComments] = useState([])
  const [clips, setClips] = useState([])
  const [alerts, setAlerts] = useState([])
  const [notifications, setNotifications] = useState([])
  const [ytId, setYtId] = useState('')
  const [alertType, setAlertType] = useState('views_threshold')
  const [alertVal, setAlertVal] = useState('')
  const [detectingClips, setDetectingClips] = useState(false)
  const [youtube, setYoutube] = useState({ configured: false, connected: false })
  const [publishing, setPublishing] = useState(false)
  const [publishMessage, setPublishMessage] = useState('')
  const [publishTitle, setPublishTitle] = useState('')
  const [publishDescription, setPublishDescription] = useState('')
  const [privacy, setPrivacy] = useState('private')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadAll()
  }, [videoId])

  async function loadAll() {
    setLoading(true)
    try {
      const [v, p, c, cl, al, n, connection] = await Promise.all([
        getVideo(videoId),
        getPackage(videoId).catch(() => null),
        getComments(videoId).catch(() => ({ comments: [] })),
        getClips(videoId).catch(() => ({ clips: [] })),
        getAlerts(videoId).catch(() => ({ alerts: [] })),
        getNotifications(videoId).catch(() => ({ notifications: [] })),
        getYouTubeConnection().catch(() => ({ configured: false, connected: false })),
      ])
      setVideo(v)
      setPkg(p)
      setComments(c.comments || [])
      setClips(cl.clips || [])
      setAlerts(al.alerts || [])
      setNotifications(n.notifications || [])
      setYoutube(connection)
      setPublishTitle(p?.titles?.[0]?.title || v.original_filename || '')
      setPublishDescription(p?.description || '')

      if (v.youtube_video_id) {
        const a = await getAnalytics(videoId).catch(() => null)
        setAnalytics(a?.stats)
      }
    } catch (err) {
      console.error(err)
    }
    setLoading(false)
  }

  async function handleLinkYt() {
    if (!ytId.trim()) return
    await linkYouTube(videoId, ytId.trim())
    const a = await getAnalytics(videoId).catch(() => null)
    setAnalytics(a?.stats)
    setVideo(v => ({ ...v, youtube_video_id: ytId.trim() }))
  }

  async function handleConnectYouTube() {
    try {
      const res = await connectYouTube()
      window.open(res.authorization_url, 'creatoros-youtube', 'width=620,height=720')
      setPublishMessage('Finish connecting your YouTube channel in the window, then refresh this dashboard.')
    } catch (err) { setPublishMessage(err.message) }
  }

  async function handlePublish() {
    setPublishing(true)
    setPublishMessage('Uploading video and captions to YouTube…')
    try {
      const result = await publishToYouTube(videoId, {
        title: publishTitle, description: publishDescription, tags: pkg?.tags || [], privacy,
      })
      setVideo(v => ({ ...v, youtube_video_id: result.youtube_video_id, status: 'published' }))
      setPublishMessage(`Published successfully. ${result.captions_uploaded ? 'Captions are attached.' : ''}`)
      window.open(result.url, '_blank', 'noopener,noreferrer')
      const a = await getAnalytics(videoId).catch(() => null)
      setAnalytics(a?.stats)
    } catch (err) { setPublishMessage(err.message) }
    setPublishing(false)
  }

  async function handleApprove(comment) {
    await approveComment(videoId, comment.id, comment.ai_draft_reply)
    setComments(cs => cs.map(c => c.id === comment.id ? { ...c, status: 'approved' } : c))
  }

  async function handleSkip(commentId) {
    await skipComment(videoId, commentId)
    setComments(cs => cs.map(c => c.id === commentId ? { ...c, status: 'skipped' } : c))
  }

  async function handleBatchApprove() {
    const result = await batchApproveComments(videoId)
    const failedIds = new Set((result.failures || []).map(f => f.comment_id))
    setComments(cs => cs.map(c => c.ai_draft_reply && !failedIds.has(c.id) ? { ...c, status: 'approved' } : c))
    if (failedIds.size) alert(`${result.approved_count} replies posted. ${failedIds.size} need attention.`)
  }

  async function handleDetectClips() {
    setDetectingClips(true)
    try {
      const res = await detectClips(videoId)
      setClips(prev => [...(res.opportunities || []), ...prev])
    } catch (e) { alert(e.message) }
    setDetectingClips(false)
  }

  async function handleClipAction(clipId, status) {
    await updateClip(videoId, clipId, status)
    setClips(cs => cs.map(c => c.id === clipId ? { ...c, status } : c))
  }

  async function handlePublishShort(clip) {
    try {
      const result = await publishShortToYouTube(videoId, clip.id, {
        title: clip.clip_package?.title || 'New Short',
        description: clip.clip_package?.description || '',
        tags: clip.clip_package?.hashtags || [],
        privacy: 'unlisted',
      })
      setClips(cs => cs.map(c => c.id === clip.id ? { ...c, status: 'published', clip_package: { ...c.clip_package, youtube_url: result.url } } : c))
    } catch (err) { alert(err.message) }
  }

  async function handleAddAlert() {
    if (!alertVal) return
    const a = await createAlert(videoId, alertType, parseFloat(alertVal))
    setAlerts(prev => [...prev, a])
    setAlertVal('')
  }

  async function handleDeleteAlert(alertId) {
    await deleteAlert(videoId, alertId)
    setAlerts(prev => prev.filter(a => a.id !== alertId))
  }

  async function handleReadNotif(id) {
    await markNotificationRead(id)
    setNotifications(prev => prev.filter(n => n.id !== id))
  }

  if (loading) return (
    <div style={{ ...s.page, textAlign: 'center', paddingTop: 100 }}>
      <div style={{ color: '#666', fontSize: 16 }}>Loading your dashboard...</div>
    </div>
  )

  const pending = comments.filter(c => c.status === 'pending')
  const pendingClips = clips.filter(c => c.status === 'pending_approval')

  return (
    <div style={s.page}>
      <nav style={s.nav}>
        <span style={s.logo}>CreatorOS</span>
        <button style={s.back} onClick={() => navigate('/')}>← Upload another</button>
      </nav>

      <div style={s.title}>{video?.original_filename || 'Your video'}</div>
      <div style={s.meta}>
        {video?.topic && `Topic: ${video.topic} · `}
        Status: {video?.status} · {notifications.length > 0 && `🔔 ${notifications.length} notification${notifications.length > 1 ? 's' : ''}`}
      </div>

      <div style={{ ...s.section, padding: 20, marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
          <div>
            <div style={s.sectionTitle}>Distribution command center</div>
            <div style={{ color: '#777', fontSize: 13 }}>One source video. Every channel. One place to act.</div>
          </div>
          {!youtube.connected && <button style={s.linkYtBtn} onClick={handleConnectYouTube}>Connect YouTube</button>}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 10, marginTop: 18 }}>
          {[
            ['YouTube', video?.youtube_video_id ? 'Published' : youtube.connected ? 'Ready to publish' : youtube.configured ? 'Connect channel' : 'OAuth setup needed'],
            ['TikTok', 'Coming next'],
            ['Instagram Reels', 'Coming next'],
          ].map(([name, status]) => (
            <div key={name} style={{ background: '#0d0d0d', border: '1px solid #222', borderRadius: 10, padding: 14 }}>
              <div style={{ color: '#eee', fontSize: 14, fontWeight: 600 }}>{name}</div>
              <div style={{ color: name === 'YouTube' && video?.youtube_video_id ? '#4ade80' : '#777', fontSize: 12, marginTop: 6 }}>{status}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Notifications bar */}
      {notifications.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          {notifications.map(n => (
            <div key={n.id} style={s.notifCard}>
              <span style={s.notifText}>{n.message}</span>
              <button style={s.deleteBtn} onClick={() => handleReadNotif(n.id)}>✕</button>
            </div>
          ))}
        </div>
      )}

      {/* Analytics strip */}
      {analytics ? (
        <div style={s.grid}>
          {[
            { num: analytics.view_count?.toLocaleString(), label: 'Views' },
            { num: analytics.like_count?.toLocaleString(), label: 'Likes' },
            { num: analytics.comment_count?.toLocaleString(), label: 'Comments' },
            { num: `${analytics.like_ratio}%`, label: 'Like ratio' },
          ].map(({ num, label }) => (
            <div key={label} style={s.statCard}>
              <div style={s.statNum}>{num}</div>
              <div style={s.statLabel}>{label}</div>
            </div>
          ))}
        </div>
      ) : (
        <div style={{ ...s.section, marginBottom: 24 }}>
          <div style={s.sectionTitle}>Link YouTube video to track analytics</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 8 }}>
            <input
              style={s.linkYtInput}
              placeholder="YouTube video ID (e.g. dQw4w9WgXcQ)"
              value={ytId}
              onChange={e => setYtId(e.target.value)}
            />
            <button style={s.linkYtBtn} onClick={handleLinkYt}>Link</button>
          </div>
          <div style={{ color: '#444', fontSize: 12, marginTop: 8 }}>
            Found in your YouTube URL: youtube.com/watch?v=<strong style={{ color: '#666' }}>VIDEO_ID</strong>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div style={s.tabs}>
        {[
          ['package', `Upload Package`],
          ['comments', `Comments ${pending.length > 0 ? `(${pending.length})` : ''}`],
          ['clips', `Clips ${pendingClips.length > 0 ? `🔥 ${pendingClips.length}` : ''}`],
          ['alerts', 'Alerts'],
        ].map(([key, label]) => (
          <button key={key} style={s.tab(tab === key)} onClick={() => setTab(key)}>{label}</button>
        ))}
      </div>

      {/* PACKAGE TAB */}
      {tab === 'package' && pkg && (
        <>
          <div style={s.section}>
            <div style={s.sectionTitle}>Ready to publish</div>
            <div style={{ color: '#777', fontSize: 13, marginBottom: 16 }}>Review the AI package, then publish the original video and captions to your connected YouTube channel.</div>
            <input style={{ ...s.linkYtInput, width: '100%', marginBottom: 10 }} value={publishTitle} onChange={e => setPublishTitle(e.target.value)} placeholder="Video title" />
            <textarea style={{ ...s.textarea, minHeight: 130 }} value={publishDescription} onChange={e => setPublishDescription(e.target.value)} />
            <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginTop: 12, flexWrap: 'wrap' }}>
              <select style={s.select} value={privacy} onChange={e => setPrivacy(e.target.value)}>
                <option value="private">Private — best for a demo</option>
                <option value="unlisted">Unlisted</option>
                <option value="public">Public</option>
              </select>
              <button style={s.batchBtn} disabled={!youtube.connected || publishing} onClick={handlePublish}>
                {publishing ? 'Publishing…' : youtube.connected ? 'Publish to YouTube' : 'Connect YouTube to publish'}
              </button>
            </div>
            {publishMessage && <div style={{ color: publishMessage.startsWith('Published') ? '#4ade80' : '#aaa', fontSize: 13, marginTop: 12 }}>{publishMessage}</div>}
          </div>

          {/* Titles */}
          <div style={s.section}>
            <div style={s.sectionTitle}>
              Title options
              <span style={{ fontSize: 12, color: '#666', fontWeight: 400, marginLeft: 8 }}>data-backed from niche research</span>
            </div>
            {(pkg.titles || []).map((t, i) => (
              <div key={i} style={s.titleOption}>
                <div style={s.rankBadge}>#{t.rank || i + 1}</div>
                <div style={s.titleText}>{t.title}</div>
                <div style={s.titleReason}>{t.reasoning}</div>
                <button style={s.copyBtn} onClick={() => copy(t.title)}>Copy</button>
              </div>
            ))}
          </div>

          {/* Description */}
          <div style={s.section}>
            <div style={s.sectionTitle}>
              Description
              <button style={s.copyBtn} onClick={() => copy(pkg.description)}>Copy all</button>
            </div>
            <textarea style={s.textarea} defaultValue={pkg.description} />
          </div>

          {/* Tags */}
          <div style={s.section}>
            <div style={s.sectionTitle}>
              Tags ({(pkg.tags || []).length})
              <button style={s.copyBtn} onClick={() => copy((pkg.tags || []).join(', '))}>Copy all</button>
            </div>
            {(pkg.tags || []).map((t, i) => <span key={i} style={s.tag}>{t}</span>)}
          </div>

          {/* Chapters */}
          <div style={s.section}>
            <div style={s.sectionTitle}>
              Chapters / Timestamps
              <button style={s.copyBtn} onClick={() => copy(pkg.chapters)}>Copy</button>
            </div>
            <textarea style={{ ...s.textarea, minHeight: 160, fontFamily: 'monospace', fontSize: 13 }} defaultValue={pkg.chapters} />
          </div>

          {/* Captions */}
          <div style={s.section}>
            <div style={s.sectionTitle}>Captions file (.srt)</div>
            <div style={{ color: '#666', fontSize: 13, marginBottom: 12 }}>
              Upload this directly to YouTube Studio under Subtitles.
            </div>
            <button style={s.downloadBtn} onClick={() => downloadSrt(pkg.srt_content, 'captions.srt')}>
              ⬇ Download captions.srt
            </button>
          </div>

          {/* Shorts moments */}
          {(pkg.shorts_moments || []).length > 0 && (
            <div style={s.section}>
              <div style={s.sectionTitle}>Recommended clip moments for Shorts</div>
              {pkg.shorts_moments.map((m, i) => (
                <div key={i} style={{ ...s.titleOption, marginBottom: 12 }}>
                  <div style={{ fontSize: 12, color: '#7c6cfc', marginBottom: 6, fontWeight: 600 }}>
                    Clip {i + 1} · {Math.floor(m.start_seconds / 60)}:{String(Math.floor(m.start_seconds % 60)).padStart(2, '0')} – {Math.floor(m.end_seconds / 60)}:{String(Math.floor(m.end_seconds % 60)).padStart(2, '0')}
                  </div>
                  <div style={s.titleText}>{m.suggested_title}</div>
                  <div style={s.titleReason}>{m.why_it_works}</div>
                  {m.standalone && <span style={{ ...s.tag, background: '#0d2e0d', color: '#4ade80', fontSize: 11 }}>✓ Standalone — no context needed</span>}
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* COMMENTS TAB */}
      {tab === 'comments' && (
        <div style={s.section}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <div style={{ ...s.sectionTitle, margin: 0 }}>
              Comment inbox · {comments.length} total · {pending.length} pending
            </div>
            {pending.length > 0 && (
              <button style={s.batchBtn} onClick={handleBatchApprove}>
                Approve all {pending.length} drafts
              </button>
            )}
          </div>

          {comments.length === 0 && <div style={s.empty}>No comments yet. Link your YouTube video to pull comments.</div>}

          {comments.filter(c => c.status === 'pending').map(c => (
            <div key={c.id} style={s.commentCard}>
              <div style={s.commenterName}>{c.commenter_name}</div>
              <div style={s.commentText}>{c.comment_text}</div>
              {c.ai_draft_reply && (
                <div style={s.draftReply}>💬 {c.ai_draft_reply}</div>
              )}
              <div style={s.commentActions}>
                <button style={s.approveBtn} onClick={() => handleApprove(c)}>✓ Approve reply</button>
                <button style={s.skipBtn} onClick={() => handleSkip(c.id)}>Skip</button>
              </div>
            </div>
          ))}

          {comments.filter(c => c.status === 'approved').length > 0 && (
            <div style={{ marginTop: 24, color: '#444', fontSize: 13 }}>
              {comments.filter(c => c.status === 'approved').length} replies approved
            </div>
          )}
        </div>
      )}

      {/* CLIPS TAB */}
      {tab === 'clips' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <div>
              <div style={{ fontSize: 16, fontWeight: 600, color: '#fff' }}>Clip opportunities</div>
              <div style={{ fontSize: 13, color: '#666', marginTop: 4 }}>Detected from comment patterns — your audience told us what to clip</div>
            </div>
            <button style={{ ...s.scheduleBtn, padding: '10px 20px' }} onClick={handleDetectClips} disabled={detectingClips}>
              {detectingClips ? 'Detecting...' : '🔍 Detect clips now'}
            </button>
          </div>

          {clips.length === 0 && (
            <div style={s.empty}>
              No clip opportunities detected yet.<br />
              <span style={{ fontSize: 12, marginTop: 8, display: 'block' }}>
                The tool scans comments every 2 hours. Click "Detect clips now" to run manually.
              </span>
            </div>
          )}

          {clips.filter(c => c.status === 'pending_approval').map(c => (
            <div key={c.id} style={s.clipCard}>
              <div style={s.clipBadge}>🔥 {c.comment_count} comments referencing this moment</div>
              <div style={s.clipTitle}>
                {c.clip_package?.title || `Clip at ${Math.floor(c.start_seconds / 60)}:${String(Math.floor(c.start_seconds % 60)).padStart(2, '0')}`}
              </div>
              <div style={s.clipWhy}>{c.why_it_resonated}</div>
              <div style={s.clipMeta}>
                Timestamp: {Math.floor(c.start_seconds / 60)}:{String(Math.floor(c.start_seconds % 60)).padStart(2, '0')} –
                {Math.floor(c.end_seconds / 60)}:{String(Math.floor(c.end_seconds % 60)).padStart(2, '0')}
                {c.clip_package?.suggested_post_time && ` · Suggested post: ${c.clip_package.suggested_post_time}`}
              </div>

              {c.clip_package?.rendered_url && (
                <video controls preload="metadata" style={{ width: '100%', maxWidth: 250, borderRadius: 8, marginBottom: 16 }} src={c.clip_package.rendered_url} />
              )}
              {c.clip_package?.render_error && <div style={{ color: '#fbbf24', fontSize: 12, marginBottom: 12 }}>Render unavailable: {c.clip_package.render_error}</div>}

              {c.clip_package && (
                <div style={{ marginBottom: 16 }}>
                  {c.clip_package.description && <div style={{ color: '#888', fontSize: 13, marginBottom: 8 }}>{c.clip_package.description}</div>}
                  {c.clip_package.hashtags && (
                    <div>{c.clip_package.hashtags.map((h, i) => <span key={i} style={s.tag}>#{h.replace('#', '')}</span>)}</div>
                  )}
                </div>
              )}

              {c.example_comments?.length > 0 && (
                <div style={{ marginBottom: 16 }}>
                  <div style={{ fontSize: 11, color: '#555', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 6 }}>Comments referencing this</div>
                  {c.example_comments.slice(0, 3).map((ec, i) => (
                    <div key={i} style={{ fontSize: 12, color: '#666', marginBottom: 4, fontStyle: 'italic' }}>"{ec}"</div>
                  ))}
                </div>
              )}

              <div style={s.clipActions}>
                {c.clip_package?.rendered_url && <button style={s.approveBtn} disabled={!youtube.connected} onClick={() => handlePublishShort(c)}>Publish Short</button>}
                <button style={s.scheduleBtn} onClick={() => handleClipAction(c.id, 'scheduled')}>Schedule post</button>
                <button style={{ ...s.approveBtn, marginLeft: 0 }} onClick={() => copy(`${c.clip_package?.title || ''}\n\n${c.clip_package?.description || ''}\n\n${(c.clip_package?.hashtags || []).join(' ')}`)}>Copy package</button>
                <button style={s.dismissBtn} onClick={() => handleClipAction(c.id, 'dismissed')}>Dismiss</button>
              </div>
            </div>
          ))}

          {clips.filter(c => c.status === 'scheduled').length > 0 && (
            <div style={{ marginTop: 24 }}>
              <div style={{ fontSize: 14, color: '#666', marginBottom: 12 }}>Scheduled clips</div>
              {clips.filter(c => c.status === 'scheduled').map(c => (
                <div key={c.id} style={{ ...s.clipCard, opacity: 0.7 }}>
                  <div style={{ fontSize: 14, color: '#7c6cfc' }}>🗓 {c.clip_package?.title || 'Clip'} — Scheduled</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ALERTS TAB */}
      {tab === 'alerts' && (
        <div style={s.section}>
          <div style={s.sectionTitle}>Alert conditions</div>
          <div style={{ color: '#666', fontSize: 13, marginBottom: 20 }}>
            We check every 30 minutes and notify you when conditions are met.
          </div>

          {alerts.map(a => (
            <div key={a.id} style={s.alertRow}>
              <span style={s.alertText}>
                {a.condition_type === 'views_threshold' && `🎉 Notify when views reach ${a.threshold_value.toLocaleString()}`}
                {a.condition_type === 'engagement_drop' && `⚠️ Notify if like ratio drops below ${a.threshold_value}%`}
                {a.condition_type === 'comment_spike' && `💬 Notify when ${a.threshold_value} comments reached`}
                {a.triggered && ' · ✓ Triggered'}
              </span>
              <button style={s.deleteBtn} onClick={() => handleDeleteAlert(a.id)}>✕</button>
            </div>
          ))}

          <div style={s.alertForm}>
            <select style={s.select} value={alertType} onChange={e => setAlertType(e.target.value)}>
              <option value="views_threshold">Views reach</option>
              <option value="engagement_drop">Engagement drops below</option>
              <option value="comment_spike">Comments reach</option>
            </select>
            <input
              style={s.input}
              type="number"
              placeholder={alertType === 'engagement_drop' ? '% e.g. 3' : 'e.g. 5000'}
              value={alertVal}
              onChange={e => setAlertVal(e.target.value)}
            />
            <button style={s.addAlertBtn} onClick={handleAddAlert}>+ Add alert</button>
          </div>
        </div>
      )}
    </div>
  )
}
