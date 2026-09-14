import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { CircleMarker, MapContainer, Popup, TileLayer } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import {
  Activity,
  ShieldAlert,
  Zap,
  Map as MapIcon,
  MapPin,
  Wrench,
  Truck,
  History as HistoryIcon,
  Bot,
  UploadCloud,
  CheckCircle2,
  AlertTriangle,
  TrendingUp,
  Search,
  ArrowRight,
  ChevronRight,
  RefreshCw,
  FileText,
  Gauge,
  Thermometer,
  Sparkles,
  Radio,
  Sliders,
  Compass,
  ArrowUpRight,
  LayoutDashboard,
  Cpu,
  CornerDownRight,
  Send,
  CloudRain
} from 'lucide-react'

const requiredColumns = [
  'transformer_id',
  'timestamp',
  'temperature_c',
  'vibration_mm_s',
  'partial_discharge_pc',
  'oil_temperature_c',
  'oil_moisture_ppm',
  'oil_acidity_mgKOH_g',
  'load_percentage',
  'voltage_kv',
  'current_a',
  'humidity_percentage',
  'rainfall_mm',
  'wind_speed_kmh',
  'pressure_hpa',
  'lightning_probability',
  'storm_probability',
  'flood_risk',
]
const sensorFields = requiredColumns.slice(2)

const navItems = [
  { id: 'Dashboard', label: 'Overview Matrix', icon: LayoutDashboard },
  { id: 'Risk Assets', label: 'Risk Asset Registry', icon: ShieldAlert },
  { id: 'Grid Map', label: 'Interactive GIS Map', icon: MapIcon },
  { id: 'Maintenance Advisor', label: 'Prescriptive Advisor', icon: Wrench },
  { id: 'Crew Deployment', label: 'Contingency Fleet', icon: Truck },
  { id: 'Check History', label: 'Telemetry Audit Log', icon: HistoryIcon },
]

// Motion variants
const pageTransition = {
  initial: { opacity: 0, y: 14 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.28, ease: [0.16, 1, 0.3, 1] } },
  exit: { opacity: 0, y: -10, transition: { duration: 0.18 } }
}

const listContainer = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.04
    }
  }
}

const listItem = {
  hidden: { opacity: 0, y: 10 },
  show: { opacity: 1, y: 0, transition: { duration: 0.2 } }
}

function App() {
  const [view, setView] = useState('Dashboard')
  const [dashboard, setDashboard] = useState({})
  const [assets, setAssets] = useState([])
  const [transformers, setTransformers] = useState([])
  const [selected, setSelected] = useState(null)
  const [flow, setFlow] = useState('idle')
  const [fileState, setFileState] = useState({ name: '', rows: [], errors: [] })
  const [manualId, setManualId] = useState('')
  const [manual, setManual] = useState(Object.fromEntries(sensorFields.map((field) => [field, ''])))

  // Gemini-backed, database-grounded AI chat state
  const [bobQuestion, setBobQuestion] = useState('')
  const [bobMessages, setBobMessages] = useState([
    {
      role: 'bob',
      text: '### 🤖 Your AI Operational Assistant\nWelcome to Grid Operations Control. I am your Ai Assistant, grounded in real-time transformer telemetry and XGBoost failure forecasting model. How can I assist with asset risk assessment, maintenance directives, or contingency fleet dispatch?',
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      provider: 'Your AI Assistant',
    },
  ])
  const [bobStatus, setBobStatus] = useState(null)
  const [bobLoading, setBobLoading] = useState(false)

  const [maintenance, setMaintenance] = useState([])
  const [crews, setCrews] = useState([])
  const [analytics, setAnalytics] = useState(null)
  const [actionTransformer, setActionTransformer] = useState(null)
  const [history, setHistory] = useState([])
  const [historyAnalysis, setHistoryAnalysis] = useState(null)

  const load = (url, setter) => fetch(url).then((res) => res.json()).then(setter)

  useEffect(() => {
    load('/api/transformers', setTransformers)
    load('/api/prediction-history', setHistory)
    load('/api/prediction-history/analysis', setHistoryAnalysis)
    load('/api/bob/status', setBobStatus)
  }, [])

  const openDetail = (id) => {
    setView('Transformer Details')
    load(`/api/transformers/${id}`, setSelected)
  }

  const chooseView = (name) => {
    setView(name)
    if (name === 'Dashboard') { setFlow('idle'); setSelected(null) }
    if (name === 'Risk Assets' || name === 'Grid Map') load('/api/risk-assets', setAssets)
    if (name === 'Maintenance Advisor') load('/api/maintenance', setMaintenance)
    if (name === 'Crew Deployment') load('/api/crew', setCrews)
    if (name === 'ML Analytics') load('/api/analytics', setAnalytics)
    if (name === 'Check History') {
      load('/api/prediction-history', setHistory)
      load('/api/prediction-history/analysis', setHistoryAnalysis)
    }
    if (name === 'AURA AI') load('/api/bob/status', setBobStatus)
  }

  const evaluate = () => { setFlow('choose'); setView('Dashboard') }

  const readCsv = (file) => {
    const reader = new FileReader()
    reader.onload = (event) => {
      const lines = event.target.result.trim().split(/\r?\n/)
      const headers = lines[0].split(',').map((item) => item.trim())
      const rows = lines.slice(1).filter(Boolean).map((line) => {
        const values = line.split(',')
        return Object.fromEntries(headers.map((header, index) => [header, values[index]?.trim()]))
      })
      const errors = requiredColumns.filter((column) => !headers.includes(column))
      setFileState({ name: file.name, rows, errors: errors.length ? [`Missing required columns: ${errors.join(', ')}`] : [] })
      setFlow('upload')
    }
    reader.readAsText(file)
  }

  const runBatch = async () => {
    const res = await fetch('/api/predict/batch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rows: fileState.rows }),
    })
    const json = await res.json()
    if (!res.ok) return setFileState((state) => ({ ...state, errors: [json.detail || 'Prediction failed'] }))
    setAssets(json)
    setSelected(json[0])
    setFlow('result')
  }

  const selectManualTransformer = (id) => {
    setManualId(id)
    setManual(Object.fromEntries(sensorFields.map((field) => [field, ''])))
  }

  const runManual = async () => {
    const missing = sensorFields.filter((field) => manual[field] === '')
    if (!manualId || missing.length) return alert(`Enter all telemetry readings before running analysis. Missing: ${missing.join(', ')}`)
    const res = await fetch('/api/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ transformer_id: manualId, timestamp: new Date().toISOString(), ...manual }),
    })
    const json = await res.json()
    if (!res.ok) return alert(json.detail || 'Prediction failed')
    setSelected(json)
    setFlow('result')
  }

  const askBob = async (customQuery) => {
    const q = customQuery || bobQuestion
    if (!q || !q.trim() || bobLoading) return

    const userTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    const userMsg = { role: 'user', text: q, time: userTime }
    setBobMessages((prev) => [...prev, userMsg])
    setBobQuestion('')
    setBobLoading(true)

    try {
      const res = await fetch('/api/bob/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q }),
      })
      const json = await res.json()
      const botTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      setBobMessages((prev) => [
        ...prev,
        {
          role: 'bob',
          text: json.answer || json.detail || 'No response from AURA AI.',
          time: botTime,
          provider: json.provider || 'AURA AI',
          model: json.model,
        },
      ])
    } catch (err) {
      setBobMessages((prev) => [
        ...prev,
        {
          role: 'bob',
          text: '⚠️ Could not reach to AI. Please ensure backend is running.',
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          provider: 'System Failure',
        },
      ])
    } finally {
      setBobLoading(false)
    }
  }

  const showMaintenance = () => { setActionTransformer(selected); chooseView('Maintenance Advisor') }

  const showCrew = async () => {
    setView('Crew Deployment')
    const res = await fetch(`/api/crew?transformer_id=${selected.transformer_id}`)
    if (res.ok) {
      const rows = await res.json()
      setCrews(rows)
      const recommended = rows.find((row) => row.recommended)
      if (recommended) {
        setActionTransformer({
          ...selected,
          crew_recommendation: {
            ...selected.crew_recommendation,
            crew_id: recommended.crew_id,
            crew_name: recommended.crew_name,
            crew_type: recommended.crew_type,
            skill_level: recommended.skill_level,
            distance_km: recommended.distance_km,
            deployment_action: selected.risk_level === 'LOW' ? 'MONITOR' : selected.risk_level === 'MEDIUM' ? 'DISPATCH CREW' : 'PRE-POSITION CREW',
            reason: `${selected.risk_level} risk requires ${recommended.crew_type} response within ${recommended.distance_km.toFixed(2)} km.`,
          },
        })
      }
    }
  }

  const showBob = () => {
    const q = `Why is ${selected?.transformer_id} risky and what action is recommended?`
    chooseView('AURA AI')
    askBob(q)
  }

  const result = selected && (
    <Result
      result={selected}
      onDetail={() => openDetail(selected.transformer_id)}
      onHistory={() => openDetail(selected.transformer_id)}
      onMaintenance={showMaintenance}
      onCrew={showCrew}
      onBob={showBob}
      onAnother={() => { setFlow('choose'); setSelected(null) }}
    />
  )

  return (
    <div className="app-shell">
      {/* Sidebar Navigation */}
      <motion.aside className="sidebar" initial={{ x: -20, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ duration: 0.3 }}>
        <div className="brand">
          <div className="brand-mark-wrapper">
            <div className="brand-mark">AG</div>
          </div>
          <div className="brand-info">
            <strong>AURA GRID</strong>
            <small>AI POWER SENTINEL</small>
          </div>
        </div>

        <nav>
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = view === item.id
            return (
              <motion.button
                key={item.id}
                whileHover={{ x: 3 }}
                whileTap={{ scale: 0.98 }}
                className={isActive ? 'nav-button active' : 'nav-button'}
                onClick={() => chooseView(item.id)}
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </motion.button>
            )
          })}
        </nav>

        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.97 }}
          className="bob-link"
          onClick={() => chooseView('AURA AI')}
        >
          <Bot size={18} />
          <span>GEMINI AI COPILOT</span>
        </motion.button>
      </motion.aside>

      {/* Main Workspace Panel */}
      <main className="main-panel">
        <header className="topbar">
          <div>
            <span className="eyebrow amber">
              <Radio size={13} /> AUTONOMOUS SUBSTATION TELEMETRY
            </span>
            <h1>{view === 'Dashboard' ? 'Grid Reliability & Anomaly Matrix' : view}</h1>
          </div>
          <div className="system-status">
            <i /> MODEL ONLINE
          </div>
        </header>

        <AnimatePresence mode="wait">
          <motion.div key={view} initial="initial" animate="animate" exit="exit" variants={pageTransition}>
            {view === 'Dashboard' && (
              <PortalDashboard
                dashboard={dashboard}
                historyAnalysis={historyAnalysis}
                evaluate={evaluate}
                flow={flow}
                setFlow={setFlow}
                fileState={fileState}
                readCsv={readCsv}
                runBatch={runBatch}
                manualId={manualId}
                setManualId={setManualId}
                onManualSelect={selectManualTransformer}
                manual={manual}
                setManual={setManual}
                runManual={runManual}
                result={result}
                transformers={transformers}
              />
            )}
            {view === 'Risk Assets' && <AssetList assets={assets} openDetail={openDetail} />}
            {view === 'Grid Map' && <MapView assets={assets} openDetail={openDetail} />}
            {view === 'Transformer Details' && (
              selected ? (
                <Detail
                  detail={selected}
                  onDetail={() => openDetail(selected.transformer_id)}
                  onHistory={() => openDetail(selected.transformer_id)}
                  onMaintenance={showMaintenance}
                  onCrew={showCrew}
                  onBob={showBob}
                  onAnother={() => { setFlow('choose'); setView('Dashboard'); setSelected(null) }}
                />
              ) : (
                <Empty text="Select an asset from the Risk Asset Registry or GIS Map to view full telemetry." />
              )
            )}
            {view === 'Maintenance Advisor' && <Maintenance rows={maintenance} openDetail={openDetail} focus={actionTransformer} />}
            {view === 'Crew Deployment' && <Crew rows={crews} focus={actionTransformer} />}
            {view === 'ML Analytics' && <Analytics data={analytics} />}
            {view === 'Check History' && <History rows={history} analysis={historyAnalysis} />}
            {view === 'AURA AI' && <Bob messages={bobMessages} question={bobQuestion} setQuestion={setBobQuestion} ask={askBob} loading={bobLoading} status={bobStatus} />}
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  )
}

function StatCard({ label, value, subtext }) {
  return (
    <motion.div className="stat-card" whileHover={{ y: -3 }} transition={{ duration: 0.15 }}>
      <span>{label}</span>
      <strong>{value}</strong>
      {subtext && <small style={{ color: 'var(--text-muted)', fontSize: '11px', marginTop: '4px', fontWeight: 600 }}>{subtext}</small>}
    </motion.div>
  )
}

function PortalDashboard({ historyAnalysis, flow, ...props }) {
  if (flow !== 'idle') return <Dashboard flow={flow} {...props} />
  return (
    <>
      <section className="hero">
        <div>
          <span className="eyebrow amber">
            <Zap size={14} /> AUTONOMOUS RISK PORTAL
          </span>
          <h2>Prevent Grid Failure.<br />Before It Disrupts.</h2>
          <p>
            Evaluate raw transformer sensor feeds and localized atmospheric conditions against our 7-day predictive XGBoost intelligence model.
          </p>
          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            className="primary"
            onClick={props.evaluate}
          >
            <span>START RISK EVALUATION</span> <ArrowRight size={18} />
          </motion.button>
        </div>
        <div className="hero-signal">
          <span>ACTIVE SESSION</span>
          <strong>{historyAnalysis?.checks || 0}</strong>
          <small>TELEMETRY CHECKS</small>
        </div>
      </section>

      <section className="stat-strip">
        <StatCard label="MONITORED ASSETS" value={props.transformers.length || '—'} subtext="Substation Nodes" />
        <StatCard label="SESSION EVALUATIONS" value={historyAnalysis?.checks || 0} subtext="Recent Run" />
        <StatCard label="UNIQUE TRANSFORMERS" value={historyAnalysis?.transformers || 0} subtext="Audit Count" />
        <StatCard label="MAX RISK ASSET" value={historyAnalysis?.highest_risk?.transformer_id || 'NOMINAL'} subtext="Priority Flag" />
      </section>

      <section className="workflow">
        <span className="eyebrow">
          <Sliders size={14} /> CONTINUOUS FIELD INTELLIGENCE
        </span>
        <h2>Precision Reliability Workflow</h2>
        <p>
          Select an asset, enter operational telemetry (DGA oil acidity, hotspot temp, partial discharge), and instantly get model failure probability, risk driver breakdowns, and optimized fleet dispatch recommendations.
        </p>
        <motion.button
          whileHover={{ x: 4 }}
          className="text-button"
          onClick={() => props.setFlow('choose')}
        >
          <span>Initiate new telemetry check</span> <ChevronRight size={16} />
        </motion.button>
      </section>
    </>
  )
}

function Dashboard({ dashboard, evaluate, flow, setFlow, fileState, readCsv, runBatch, manualId, setManualId, onManualSelect, manual, setManual, runManual, result, transformers }) {
  return (
    <>
      {flow === 'idle' && (
        <>
          <section className="hero">
            <div>
              <span className="eyebrow amber">DECISION SUPPORT • LIVE TELEMETRY</span>
              <h2>Predictive Substation<br />Equipment Intelligence</h2>
              <p>Identify thermal stress, insulation breakdown, and atmospheric vulnerability with real-time risk scoring.</p>
              <motion.button whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }} className="primary" onClick={evaluate}>
                <span>RUN TELEMETRY CHECK</span> <ArrowRight size={18} />
              </motion.button>
            </div>
            <div className="hero-signal">
              <span>7-DAY OUTLOOK</span>
              <strong>{dashboard.overall_grid_risk || 'LOW'}</strong>
              <small>GRID RISK INDEX</small>
            </div>
          </section>

          <section className="stat-strip">
            <StatCard label="TOTAL TRANSFORMERS" value={dashboard.total_transformers ?? '—'} />
            <StatCard label="HIGH RISK ALERTS" value={dashboard.predicted_failures ?? '0'} />
            <StatCard label="DISPATCH CREWS READY" value={dashboard.available_crews ?? '—'} />
            <StatCard label="MODEL STATUS" value="ONLINE" subtext="Production Pipeline" />
          </section>

          <div className="risk-bars-container">
            <div className="section-heading">
              <div>
                <span className="eyebrow"><Activity size={14} /> ASSET HEALTH DISTRIBUTION</span>
                <h3>Substation Risk Heatmap</h3>
              </div>
              <motion.button whileHover={{ x: 3 }} className="text-button" onClick={() => setFlow('choose')}>
                <span>Run asset evaluation</span> <ChevronRight size={16} />
              </motion.button>
            </div>
            <div className="risk-bars">
              {['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((level) => {
                const count = dashboard.risk_counts?.[level] || 0
                const total = Math.max(1, dashboard.total_transformers || 1)
                const pct = Math.min(100, Math.round((count / total) * 100))
                return (
                  <div className="risk-bar-item" key={level}>
                    <span className="risk-label">
                      <span className={`risk-badge ${level.toLowerCase()}`}>{level}</span>
                    </span>
                    <div className="risk-bar-track">
                      <motion.div
                        className={`risk-bar-fill ${level.toLowerCase()}`}
                        initial={{ width: 0 }}
                        animate={{ width: `${pct}%` }}
                        transition={{ duration: 0.6, ease: 'easeOut' }}
                      />
                    </div>
                    <span className="risk-bar-count">{count}</span>
                  </div>
                )
              })}
            </div>
          </div>
        </>
      )}

      {flow === 'choose' && (
        <section className="workflow">
          <motion.button whileHover={{ x: -3 }} className="back" onClick={() => setFlow('idle')}>
            ← Back to Overview
          </motion.button>
          <span className="eyebrow amber">STEP 1 • TELEMETRY SOURCE</span>
          <h2>Select Data Ingestion Method</h2>
          <div className="choice-grid">
            <motion.button whileHover={{ y: -4 }} whileTap={{ scale: 0.98 }} className="choice-card" onClick={() => setFlow('upload')}>
              <strong>METHOD 01</strong>
              <span>BULK CSV FEED</span>
              <small>Upload batch sensor logs & weather parameters for multi-node failure risk evaluation.</small>
            </motion.button>
            <motion.button whileHover={{ y: -4 }} whileTap={{ scale: 0.98 }} className="choice-card" onClick={() => setFlow('manual')}>
              <strong>METHOD 02</strong>
              <span>MANUAL TELEMETRY</span>
              <small>Input instantaneous thermal, oil gas, and electrical readings for a single asset check.</small>
            </motion.button>
          </div>
        </section>
      )}

      {flow === 'upload' && <Upload fileState={fileState} readCsv={readCsv} runBatch={runBatch} setFlow={setFlow} />}
      {flow === 'manual' && <Manual transformers={transformers} id={manualId} setId={onManualSelect} values={manual} setValues={setManual} submit={runManual} setFlow={setFlow} />}
      {flow === 'result' && result}
    </>
  )
}

function Upload({ fileState, readCsv, runBatch, setFlow }) {
  return (
    <section className="workflow">
      <motion.button whileHover={{ x: -3 }} className="back" onClick={() => setFlow('choose')}>
        ← Choose input method
      </motion.button>
      <span className="eyebrow amber">INGESTION • BATCH TELEMETRY</span>
      <h2>Upload Substation Readings CSV</h2>
      <label className="dropzone">
        <input type="file" accept=".csv" onChange={(event) => event.target.files[0] && readCsv(event.target.files[0])} />
        <UploadCloud size={44} color="var(--accent-blue)" />
        <strong>{fileState.name || 'Click or drag CSV telemetry file here'}</strong>
        <small>Validates 16 critical columns including oil acidity, partial discharge, moisture, and storm risk.</small>
      </label>
      {fileState.name && (
        <div className={fileState.errors.length ? 'validation error' : 'validation'}>
          <strong>{fileState.errors.length ? 'SCHEMA VALIDATION ERROR' : 'VALIDATION READY'}</strong>
          <span>{fileState.errors.length ? fileState.errors[0] : `${fileState.rows.length} valid telemetry rows detected in ${fileState.name}`}</span>
        </div>
      )}
      {fileState.rows.length > 0 && !fileState.errors.length && (
        <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} className="primary" onClick={runBatch}>
          <span>EXECUTE MODEL INFERENCE</span> <ArrowRight size={18} />
        </motion.button>
      )}
    </section>
  )
}

function Manual({ transformers, id, setId, values, setValues, submit, setFlow }) {
  return (
    <section className="workflow">
      <motion.button whileHover={{ x: -3 }} className="back" onClick={() => setFlow('choose')}>
        ← Choose input method
      </motion.button>
      <span className="eyebrow amber">MANUAL INPUT • REAL-TIME SENSOR</span>
      <h2>Single Transformer Telemetry Check</h2>
      <label className="field wide">
        <span>TARGET TRANSFORMER ASSET</span>
        <select value={id} onChange={(event) => setId(event.target.value)}>
          <option value="">Select transformer ID</option>
          {transformers.map((item) => (
            <option key={item.transformer_id}>{item.transformer_id}</option>
          ))}
        </select>
      </label>
      {id && (
        <>
          <div className="asset-context">
            {(() => {
              const asset = transformers.find((item) => item.transformer_id === id)
              if (!asset) return null
              return (
                <>
                  <strong>{asset.manufacturer} {asset.transformer_type}</strong>
                  <span>Substation {asset.substation_id} • {asset.capacity_kva} kVA • {asset.age_years} yrs in service • {asset.customer_count} connected customers</span>
                </>
              )
            })()}
          </div>
          <div className="field-grid">
            {sensorFields.map((field) => (
              <label className="field" key={field}>
                <span>{field.replaceAll('_', ' ').toUpperCase()}</span>
                <input
                  type="number"
                  step="any"
                  placeholder="0.0"
                  value={values[field]}
                  onChange={(event) => setValues({ ...values, [field]: event.target.value })}
                  required
                />
              </label>
            ))}
          </div>
          <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} className="primary" onClick={submit}>
            <span>RUN RISK ANALYSIS</span> <ArrowRight size={18} />
          </motion.button>
        </>
      )}
    </section>
  )
}

function Result({ result, onDetail, onHistory, onMaintenance, onCrew, onBob, onAnother }) {
  return (
    <motion.section className="result" initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.3 }}>
      <div className="result-head">
        <div>
          <span className="eyebrow amber">PREDICTIVE DIAGNOSIS • 7-DAY OUTLOOK</span>
          <h2>Asset {result.transformer_id}</h2>
        </div>
        <span className={`risk-badge ${String(result.risk_level || 'MEDIUM').toLowerCase()}`}>
          {result.risk_level || 'MEDIUM'}
        </span>
      </div>

      <div className="result-score">
        <div className="result-score-left">
          <strong>{result.failure_probability}%</strong>
          <span>FAILURE PROBABILITY SCORE</span>
        </div>
        <b>PRIORITY: {result.priority || 'PENDING'} • COMPOSITE SCORE {result.risk_score ?? '—'}</b>
      </div>

      <div className="detail-grid">
        <div>
          <span>GRID IMPACT INDEX</span>
          <strong>{result.grid_impact ?? '—'}%</strong>
        </div>
        <div>
          <span>WEATHER VULNERABILITY</span>
          <strong>{result.weather_risk ?? '—'}%</strong>
        </div>
        <div>
          <span>PRIMARY RISK DRIVERS</span>
          <strong>{result.reasons?.join(' • ') || 'Inspected nominal state'}</strong>
        </div>
      </div>

      <div className="recommendations">
        <div>
          <span>RECOMMENDED PREVENTATIVE MAINTENANCE</span>
          <p>{result.maintenance_recommendation || 'No immediate emergency maintenance required.'}</p>
        </div>
        <div>
          <span>OPTIMIZED CREW FLEET DISPATCH</span>
          <p>
            {result.crew_recommendation?.crew_name || 'No valid crew available'}{' '}
            <small>{result.crew_recommendation?.deployment_action}</small>
          </p>
        </div>
      </div>

      <div className="action-row">
        <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.97 }} onClick={onDetail}>
          <FileText size={14} /> VIEW TELEMETRY
        </motion.button>
        <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.97 }} onClick={onMaintenance}>
          <Wrench size={14} /> MAINTENANCE PLAN
        </motion.button>
        <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.97 }} onClick={onCrew}>
          <Truck size={14} /> CREW DISPATCH
        </motion.button>
        <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.97 }} onClick={onBob}>
          <Bot size={14} /> ASK GEMINI AI
        </motion.button>
        <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.97 }} onClick={onAnother}>
          <RefreshCw size={14} /> EVALUATE ANOTHER
        </motion.button>
      </div>
    </motion.section>
  )
}

function AssetList({ assets, openDetail }) {
  const [query, setQuery] = useState('')
  const [sort, setSort] = useState('risk_score')
  const filtered = assets
    .filter((item) => item.transformer_id.toLowerCase().includes(query.toLowerCase()))
    .sort((a, b) => (b[sort] || 0) - (a[sort] || 0))

  return (
    <section className="data-view">
      <div className="toolbar">
        <div style={{ position: 'relative', flex: 1 }}>
          <input
            placeholder="Search by Transformer ID or Substation..."
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </div>
        <select value={sort} onChange={(event) => setSort(event.target.value)}>
          <option value="risk_score">Sort: Composite Risk Score</option>
          <option value="failure_probability">Sort: Failure Probability</option>
          <option value="grid_impact">Sort: Grid Impact Index</option>
        </select>
      </div>

      <table>
        <thead>
          <tr>
            <th>TRANSFORMER ASSET</th>
            <th>RISK LEVEL</th>
            <th>7-DAY FAILURE PROBABILITY</th>
            <th>SCORE</th>
            <th>PRIORITY RANK</th>
          </tr>
        </thead>
        <motion.tbody variants={listContainer} initial="hidden" animate="show">
          {filtered.map((item) => (
            <motion.tr key={item.transformer_id} variants={listItem} onClick={() => openDetail(item.transformer_id)}>
              <td>
                <strong>{item.transformer_id}</strong>
                <small>{item.asset?.substation_id} Substation</small>
              </td>
              <td>
                <span className={`risk-badge ${(item.risk_level || 'MEDIUM').toLowerCase()}`}>{item.risk_level || 'MEDIUM'}</span>
              </td>
              <td>
                <strong>{item.failure_probability}%</strong>
              </td>
              <td>{item.risk_score}</td>
              <td>{item.priority}</td>
            </motion.tr>
          ))}
        </motion.tbody>
      </table>
    </section>
  )
}

function MapView({ assets, openDetail }) {
  const uniqueAssets = Array.from(
    new Map(
      assets
        .filter((item) => Number.isFinite(Number(item.asset?.latitude)) && Number.isFinite(Number(item.asset?.longitude)))
        .map((item) => [item.transformer_id, item])
    ).values()
  )
  const center = uniqueAssets.length ? [Number(uniqueAssets[0].asset.latitude), Number(uniqueAssets[0].asset.longitude)] : [22.9, 72.7]

  return (
    <section className="map-view">
      <MapContainer center={center} zoom={10} scrollWheelZoom className="real-map">
        <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        {uniqueAssets.map((item) => (
          <CircleMarker
            key={item.transformer_id}
            center={[Number(item.asset.latitude), Number(item.asset.longitude)]}
            pathOptions={{ color: riskColor(item.risk_level), fillColor: riskColor(item.risk_level), fillOpacity: 0.85 }}
            radius={10}
          >
            <Popup>
              <strong>{item.transformer_id}</strong>
              <br />
              {item.risk_level} • {item.failure_probability}% Failure Prob
              <br />
              Score {item.risk_score}
              <br />
              <button className="map-detail" onClick={() => openDetail(item.transformer_id)}>
                VIEW TELEMETRY →
              </button>
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>
      <div className="map-key">
        <MapPin size={16} color="var(--accent-blue)" /> Substation Geolocation GIS • {uniqueAssets.length} active node pins monitored
      </div>
    </section>
  )
}

function riskColor(level) {
  return { CRITICAL: '#E11D48', HIGH: '#D97706', MEDIUM: '#059669', LOW: '#64748B' }[level] || '#94A3B8'
}

const Empty = ({ text }) => <div className="empty">{text}</div>

function Detail({ detail, onDetail, onHistory, onMaintenance, onCrew, onBob, onAnother }) {
  return (
    <section className="data-view">
      <div className="result-head">
        <div>
          <span className="eyebrow amber">TRANSFORMER TELEMETRY DOSSIER</span>
          <h2>Asset {detail.transformer_id}</h2>
        </div>
        <span className={`risk-badge ${(detail.risk_level || 'MEDIUM').toLowerCase()}`}>{detail.risk_level}</span>
      </div>

      <div className="asset-context">
        <strong>{detail.asset?.manufacturer} • {detail.asset?.transformer_type}</strong>
        <span>Substation {detail.asset?.substation_id} • {detail.asset?.capacity_kva} kVA • {detail.asset?.customer_count} customer nodes • {detail.asset?.age_years} yrs service</span>
      </div>

      <Result result={detail} onDetail={onDetail} onHistory={onHistory} onMaintenance={onMaintenance} onCrew={onCrew} onBob={onBob} onAnother={onAnother} />

      <h3 style={{ marginTop: '32px', marginBottom: '16px' }}>Sensor Telemetry Log</h3>
      <table>
        <thead>
          <tr>
            <th>TIMESTAMP</th>
            <th>TEMP (°C)</th>
            <th>VIBRATION (MM/S)</th>
            <th>PARTIAL DISCHARGE (PC)</th>
            <th>LOAD (%)</th>
          </tr>
        </thead>
        <tbody>
          {(detail.sensor_history || []).map((row) => (
            <tr key={row.timestamp}>
              <td>{row.timestamp}</td>
              <td>{row.temperature_c}°C</td>
              <td>{row.vibration_mm_s} mm/s</td>
              <td>{row.partial_discharge_pc} pC</td>
              <td>{row.load_percentage}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}

function Maintenance({ rows, openDetail, focus }) {
  const visible = focus ? rows.filter((row) => row.transformer_id === focus.transformer_id) : rows
  return (
    <section className="data-view">
      <h3>Prescriptive Maintenance Directives</h3>
      {visible.length === 0 && <Empty text="No transformer checks yet. Run a risk evaluation to view maintenance directives." />}
      {visible.map((row) => (
        <motion.button
          whileHover={{ y: -2 }}
          className="queue-row"
          key={`${row.transformer_id}-${row.checked_at}`}
          onClick={() => openDetail(row.transformer_id)}
        >
          <strong>{row.transformer_id}</strong>
          <span>{row.maintenance_required ? row.urgency : 'NOMINAL CONDITION'}</span>
          <p>{row.recommended_action}</p>
          <small>{row.why} • {row.failure_probability}% Failure Probability</small>
        </motion.button>
      ))}
    </section>
  )
}

function Crew({ rows, focus }) {
  const recommendation = focus?.crew_recommendation
  return (
    <section className="data-view">
      <h3>Contingency Fleet & Deployment Logistics</h3>
      {focus && (
        <div className="asset-context">
          <strong>Recommended Crew for {focus.transformer_id}: {recommendation?.crew_name || 'No valid crew found'}</strong>
          <span>ACTION: {recommendation?.deployment_action || 'NO ACTION'} • {recommendation?.reason || 'No available crew meets proximity constraints.'}</span>
        </div>
      )}
      {rows.map((row) => (
        <div className="crew-row" key={row.crew_id}>
          <div>
            <strong>{row.crew_name}</strong>
            {row.recommended && <small style={{ color: 'var(--accent-blue)', display: 'block', fontWeight: 700 }}>RECOMMENDED DISPATCH</small>}
          </div>
          <span>{row.crew_type} • Skill Level {row.skill_level}</span>
          <span>{row.distance_km ?? '—'} km away (Max {row.max_distance_km} km)</span>
          <b>{row.eligible ? 'ELIGIBLE' : row.available ? 'Available' : 'Unavailable'}</b>
        </div>
      ))}
    </section>
  )
}

function Analytics({ data }) {
  return (
    <section className="data-view">
      {data && (
        <>
          <div className="analytics-head">
            <div>
              <span className="eyebrow amber">XGBOOST PRODUCTION ARCHITECTURE</span>
              <h2>{data.model_name}</h2>
            </div>
            <div className="system-status">DECISION THRESHOLD {data.threshold}</div>
          </div>
          <h3 style={{ marginTop: '24px', marginBottom: '16px' }}>Feature Importance Metrics</h3>
          {data.feature_importance.map((item) => (
            <div className="importance" key={item.feature}>
              <span>{item.feature.replaceAll('_', ' ').toUpperCase()}</span>
              <motion.b
                initial={{ width: 0 }}
                animate={{ width: `${Math.max(2, item.importance * 100)}%` }}
                transition={{ duration: 0.5 }}
              />
              <em>{(item.importance * 100).toFixed(1)}%</em>
            </div>
          ))}
        </>
      )}
    </section>
  )
}

function History({ rows, analysis }) {
  return (
    <section className="data-view">
      <div className="analytics-head">
        <div>
          <span className="eyebrow amber">AUDIT LOG • SESSION CHECKS</span>
          <h2>Telemetry Audit History</h2>
        </div>
        <div className="system-status">{analysis?.checks || 0} COMPLETED CHECKS</div>
      </div>

      {analysis && (
        <div className="stat-strip" style={{ marginTop: '20px' }}>
          <StatCard label="TRANSFORMERS CHECKED" value={analysis.transformers} />
          <StatCard label="AVG FAILURE PROBABILITY" value={`${analysis.average_failure_probability}%`} />
          <StatCard label="HIGHEST RISK ASSET" value={analysis.highest_risk?.transformer_id || '—'} />
          <StatCard label="PEAK RISK LEVEL" value={analysis.highest_risk?.risk_level || '—'} />
        </div>
      )}

      {rows.length === 0 ? (
        <Empty text="No evaluation history recorded. Execute a manual or batch CSV check to generate audit logs." />
      ) : (
        <table>
          <thead>
            <tr>
              <th>TIMESTAMP</th>
              <th>TRANSFORMER</th>
              <th>FAILURE PROBABILITY</th>
              <th>RISK STATUS</th>
              <th>PRIORITY</th>
              <th>MAINTENANCE DIRECTIVE</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={`${row.checked_at}-${row.transformer_id}`}>
                <td>{new Date(row.checked_at).toLocaleString()}</td>
                <td><strong>{row.transformer_id}</strong></td>
                <td><strong>{row.failure_probability}%</strong></td>
                <td><span className={`risk-badge ${(row.risk_level || 'MEDIUM').toLowerCase()}`}>{row.risk_level}</span></td>
                <td>{row.priority}</td>
                <td>{row.maintenance_recommendation}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}

function renderFormattedText(text) {
  if (!text) return null
  const lines = text.split('\n')
  return lines.map((line, i) => {
    let formatted = line
    if (formatted.startsWith('### ')) {
      return <h3 key={i}>{formatInline(formatted.replace('### ', ''))}</h3>
    }
    if (formatted.trim().startsWith('- ') || formatted.trim().startsWith('* ')) {
      const cleanLine = formatted.trim().replace(/^[-*]\s+/, '')
      return <li key={i}>{formatInline(cleanLine)}</li>
    }
    if (formatted.trim() === '') return <br key={i} />
    return <p key={i}>{formatInline(formatted)}</p>
  })
}

function formatInline(str) {
  const parts = str.split(/(\*\*.*?\*\*|`.*?`)/g)
  return parts.map((part, idx) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={idx}>{part.slice(2, -2)}</strong>
    }
    if (part.startsWith('`') && part.endsWith('`')) {
      return <code key={idx}>{part.slice(1, -1)}</code>
    }
    return part
  })
}

function Bob({ messages, question, setQuestion, ask, loading, status }) {
  const chips = [
    'Why is TR068 high risk?',
    'Identify top critical transformers',
    'Which transformers need urgent maintenance?',
    'Show available dispatch crews',
    'Summarize overall grid health matrix',
  ]

  return (
    <section className="bob-chat-container">
      <div className="bob-header">
        <div>
          <span className="eyebrow amber">
            <Bot size={14} /> AI ASSISTANCE • CONTROL ROOM ADVISOR
          </span>
          <h2>Autonomous Operations Desk</h2>
        </div>
        <div className="bob-status-badge">
          <span className="dot" />
          <div>
            <strong>{status?.provider || 'AURA AI'}</strong>
            <small>{status?.model || 'Gemini'}</small>
          </div>
        </div>
      </div>

      <div className="bob-prompt-chips">
        {chips.map((chip) => (
          <motion.button
            key={chip}
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            className="chip"
            onClick={() => ask(chip)}
          >
            ⚡ {chip}
          </motion.button>
        ))}
      </div>

      <div className="bob-messages-stream">
        {messages.map((msg, idx) => (
          <motion.div
            key={idx}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
            className={`message-bubble ${msg.role}`}
          >
            <div className="message-meta">
              <strong>{msg.role === 'user' ? 'GRID OPERATOR' : 'AURA AI'}</strong>
              <small>{msg.time}</small>
              {msg.provider && <span className="provider-tag">{msg.provider}</span>}
            </div>
            <div className="message-content">{renderFormattedText(msg.text)}</div>
          </motion.div>
        ))}
        {loading && (
          <div className="message-bubble bob loading">
            <div className="typing-indicator">
              <div className="typing-dots"><span /><span /><span /></div>
              <span>Your AI is analyzing telemetry & running inference...</span>
            </div>
          </div>
        )}
      </div>

      <div className="bob-input-bar">
        <textarea
          placeholder="Ask Gemini about evaluated transformer data (e.g. What is the status of TR068?)..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              ask()
            }
          }}
        />
        <motion.button
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
          className="primary"
          onClick={() => ask()}
          disabled={loading}
        >
          <span>SEND</span> <Send size={16} />
        </motion.button>
      </div>
    </section>
  )
}

export default App
