import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import axios from 'axios';
import * as THREE from 'three';
import {
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { Routes, Route, Link } from 'react-router-dom';
import VehicleSimulatorPanel from './VehicleSimulatorPanel';
import { useWebSocket } from './useWebSocket';
import V2GEarningsWidget from './V2GEarningsWidget';
import NotificationLayer from './NotificationLayer';
import OnboardingTour from './OnboardingTour';
import TransformerHeatmap from './TransformerHeatmap';
import History from './History';
import Admin from './Admin';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// ─── Helpers ─────────────────────────────────────────────────────────────────
const pad = (n) => String(n).padStart(2, '0');

// Fix BUG-F2: Create useClock hook
function useClock() {
  const [time, setTime] = useState('');
  
  useEffect(() => {
    const update = () => {
      const d = new Date();
      setTime(`${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`);
    };
    update();
    const t = setInterval(update, 1000);
    return () => clearInterval(t);
  }, []);
  
  return time;
}

const getTimestamp = () => {
  const d = new Date();
  return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
};

// Map backend scenario slug → human label
const SCENARIO_LABELS = {
  normal:          '🌤 NORMAL',
  building_stress: '📈 BUILDING',
  peak_stress:     '🔴 PEAK',
  recovery:        '📉 RECOVERY',
};

// ─── Gauge ────────────────────────────────────────────────────────────────────
function GSIGauge({ score }) {
  const r    = 80;
  const circ = Math.PI * r;
  const dash = (score / 100) * circ;
  const gap  = circ - dash;

  const color =
    score <= 40 ? '#16a34a'
    : score <= 74 ? '#eab308'
    : '#dc2626';

  const label =
    score <= 30 ? 'LOW STRESS'
    : score <= 55 ? 'MODERATE'
    : score <= 75 ? 'HIGH STRESS'
    : 'CRITICAL';

  return (
    <div className="gauge-wrapper" style={{ height: '140px', overflow: 'hidden' }}>
      <svg width="200" height="120" viewBox="0 0 200 120">
        <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="#1a1a1a" strokeWidth="16" strokeLinecap="round" />
        <path
          d="M 20 100 A 80 80 0 0 1 180 100"
          fill="none"
          stroke={color}
          strokeWidth="16"
          strokeDasharray={`${dash} ${gap}`}
          strokeDashoffset="0"
          strokeLinecap="round"
          style={{ transition: 'stroke-dasharray 0.8s cubic-bezier(0.4,0,0.2,1), stroke 0.8s ease' }}
        />
        <text x="100" y="85"  textAnchor="middle" fill="white" fontSize="38"
              fontFamily="'IBM Plex Mono',monospace" fontWeight="700">
          {score.toFixed(0)}
        </text>
        <text x="100" y="115" textAnchor="middle" fill={color} fontSize="12"
              fontFamily="'IBM Plex Mono',monospace" letterSpacing="2" fontWeight="bold">
          {label}
        </text>
      </svg>
    </div>
  );
}

// ─── Sub-components ───────────────────────────────────────────────────────────
function StatCard({ label, value, unit, sub, accent }) {
  return (
    <div className={['stat-card', accent ? 'stat-card--accent' : ''].filter(Boolean).join(' ')}>
      <div className="stat-label">{label}</div>
      <div className="stat-value">
        {value}
        {unit && <span className="stat-unit"> {unit}</span>}
      </div>
      {sub && <div className="stat-sub">{sub}</div>}
    </div>
  );
}

function LogEntry({ time, msg, type }) {
  return (
    <div className={`log-entry log-entry--${type}`}>
      <span className="log-time">{time}</span>
      <span className="log-msg">{msg}</span>
    </div>
  );
}

function SessionRow({ id, power, time, isV2g, index, onEscalate }) {
  return (
    <div className={`session-card ${isV2g ? 'v2g-active' : ''}`} style={{ animationDelay: `${index * 60}ms` }}>
      <span className="session-id">{id}</span>
      <span className="session-power">{power.toFixed(1)} kW</span>
      <span className="session-time">{time} min</span>
      <div className="session-status-wrap">
        {isV2g ? <span className="badge badge-v2g">⚡ V2G</span> : <span className="badge badge-charging">● CHG</span>}
        <button className="btn btn-sm btn-danger btn-p0" onClick={() => onEscalate(id)} title="Escalate to P0">
          P0
        </button>
      </div>
    </div>
  );
}

function Bar({ value, max = 100, label }) {
  const pct = Math.min(100, (value / max) * 100);
  return (
    <div className="bar-wrap">
      <div className="bar-header">
        <span>{label}</span>
        <span>{value.toFixed(1)}</span>
      </div>
      <div className="bar-track">
        <div className="bar-fill" style={{ width: `${pct}%`, transition: 'width 0.8s ease' }} />
      </div>
    </div>
  );
}

function ThreeGridScene({ intensity = 0.4 }) {
  const mountRef = useRef(null);

  useEffect(() => {
    if (!mountRef.current) return undefined;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color('#030303');
    const camera = new THREE.PerspectiveCamera(60, 1, 0.1, 1000);
    camera.position.z = 4.5;

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(window.devicePixelRatio || 1);
    mountRef.current.appendChild(renderer.domElement);

    const ambient = new THREE.AmbientLight(0xffffff, 0.35 + intensity * 0.5);
    scene.add(ambient);

    const point = new THREE.PointLight(0xffffff, 1.8, 100);
    point.position.set(3, 3, 4);
    scene.add(point);

    const core = new THREE.Mesh(
      new THREE.IcosahedronGeometry(1.0, 1),
      new THREE.MeshStandardMaterial({
        color: new THREE.Color(`hsl(${Math.max(0, 120 - intensity * 120)}, 70%, 60%)`),
        metalness: 0.4,
        roughness: 0.3,
      }),
    );
    scene.add(core);

    const wire = new THREE.Mesh(
      new THREE.IcosahedronGeometry(1.35, 2),
      new THREE.MeshBasicMaterial({
        color: 0x9a9a9a,
        wireframe: true,
        transparent: true,
        opacity: 0.55,
      }),
    );
    scene.add(wire);

    const grid = new THREE.GridHelper(8, 20, 0x444444, 0x202020);
    grid.position.y = -1.7;
    scene.add(grid);

    const resize = () => {
      if (!mountRef.current) return;
      const w = mountRef.current.clientWidth;
      const h = mountRef.current.clientHeight;
      renderer.setSize(w, h);
      camera.aspect = w / Math.max(h, 1);
      camera.updateProjectionMatrix();
    };
    resize();
    window.addEventListener('resize', resize);

    let frameId;
    const animate = () => {
      frameId = requestAnimationFrame(animate);
      core.rotation.x += 0.004 + intensity * 0.002;
      core.rotation.y += 0.006 + intensity * 0.002;
      wire.rotation.y -= 0.002;
      wire.rotation.x += 0.001;
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(frameId);
      window.removeEventListener('resize', resize);
      renderer.dispose();
      if (mountRef.current?.contains(renderer.domElement)) {
        mountRef.current.removeChild(renderer.domElement);
      }
    };
  }, [intensity]);

  return <div className="three-wrap" ref={mountRef} />;
}

// ─── Main App ─────────────────────────────────────────────────────────────────
export default function App() {
  const wsData = useWebSocket();
  const clock  = useClock();
  const [gridStatus, setGridStatus] = useState(null);
  const [sessions,   setSessions]   = useState({ total_active: 0, queued: 0, sessions: [] });
  const [v2g,        setV2g]        = useState({
    registered_vehicles: 0, active_discharges: 0,
    current_v2g_capacity_kw: 0, total_compensation_paid: 0,
  });
  const [log,     setLog]     = useState([]);
  const [healthy, setHealthy] = useState(null);
  const [busy,    setBusy]    = useState(false);   // button debounce
  const [historyData, setHistoryData] = useState([]);
  const [externalSignals, setExternalSignals] = useState({
    online: false, temperature_c: null, wind_speed_kmh: null, cloud_cover_pct: null, updated_at: null,
  });
  const logRef = useRef([]);
  const prevGsi = useRef(null);
  // Fix BUG-F6: Track v2g_enabled with a ref
  const prevV2gEnabled = useRef(false);

  const addLog = useCallback((msg, type = 'info') => {
    const entry = { time: getTimestamp(), msg, type };
    logRef.current = [entry, ...logRef.current].slice(0, 40);
    setLog([...logRef.current]);
  }, []);

  // ── Fetchers ─────────────────────────────────────────────────────────────

  const fetchHealth = useCallback(async () => {
    try {
      await axios.get(`${API_URL}/api/health/`, { timeout: 5000 });
      setHealthy(true);
    } catch {
      setHealthy(false);
    }
  }, []);

  /** Pure GET — reads live simulator state, no random inputs */
  const fetchGrid = useCallback(async () => {
    try {
      const res = await axios.get(`${API_URL}/api/grid/status`, { timeout: 5000 });
      const d   = res.data;

      // Log scenario transitions
      if (prevGsi.current !== null) {
        const diff = d.gsi_score - prevGsi.current;
        if (Math.abs(diff) > 8) {
          addLog(
            `GSI ${diff > 0 ? '▲' : '▼'} ${Math.abs(diff).toFixed(1)} → ${d.gsi_score.toFixed(1)} [${SCENARIO_LABELS[d.scenario] ?? d.scenario}]`,
            d.gsi_score > 75 ? 'critical' : d.gsi_score > 55 ? 'warn' : 'info',
          );
        }
        
        // Fix BUG-F6: Use prevV2gEnabled ref
        if (d.v2g_enabled && !prevV2gEnabled.current) {
          addLog('🔴 V2G DISCHARGE MODE ACTIVATED — critical grid stress', 'critical');
        }
      }
      
      prevGsi.current = d.gsi_score;
      prevV2gEnabled.current = d.v2g_enabled;
      setGridStatus(d);
    } catch {
      addLog('Grid API unreachable — is the backend running?', 'error');
    }
  }, [addLog]);

  const fetchSessions = useCallback(async () => {
    try {
      const res = await axios.get(`${API_URL}/api/charging/active-sessions`, { timeout: 5000 });
      setSessions(res.data);
    } catch {}
  }, []);

  const fetchV2G = useCallback(async () => {
    try {
      const res = await axios.get(`${API_URL}/api/v2g/status`, { timeout: 5000 });
      setV2g(res.data);
    } catch {}
  }, []);

  const fetchHistoryData = useCallback(async () => {
    try {
      const res = await axios.get(`${API_URL}/api/grid/history?limit=80`, { timeout: 5000 });
      setHistoryData(res.data.points || []);
    } catch {}
  }, []);

  const fetchExternalSignals = useCallback(async () => {
    try {
      const res = await axios.get(`${API_URL}/api/grid/external-signals`, { timeout: 5000 });
      setExternalSignals(res.data);
    } catch {}
  }, []);

  // ── Lifecycle ─────────────────────────────────────────────────────────────

  useEffect(() => {
    fetchHealth();
    fetchGrid();
    fetchSessions();
    fetchV2G();
    fetchHistoryData();
    fetchExternalSignals();
    addLog('GridCharge dashboard connected', 'info');
    addLog(`API endpoint: ${API_URL}`, 'info');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const t = setInterval(() => {
      fetchGrid();
      fetchSessions();
      fetchV2G();
      fetchHistoryData();
      fetchExternalSignals();
    }, 3000);
    const h = setInterval(fetchHealth, 15000);
    return () => { clearInterval(t); clearInterval(h); };
  }, [fetchGrid, fetchSessions, fetchV2G, fetchHealth, fetchHistoryData, fetchExternalSignals]);

  // ── User actions ──────────────────────────────────────────────────────────

  /** Request a random EV arrival via the real backend endpoint */
  const simulateEV = async () => {
    if (busy) return;
    setBusy(true);
    const id     = `EV-${String(Math.floor(Math.random() * 9000) + 1000)}`;
    const soc    = Math.floor(Math.random() * 55) + 10;
    const target = Math.min(100, soc + Math.floor(Math.random() * 45) + 20);
    const dep    = new Date(Date.now() + (60 + Math.random() * 120) * 60000).toISOString();
    try {
      const res = await axios.post(`${API_URL}/api/charging/request-slot`, {
        vehicle_id:         id,
        soc_percent:        soc,
        target_soc_percent: target,
        departure_time:     dep,
        user_priority:      Math.floor(Math.random() * 4) + 1,
        is_v2g_capable:     Math.random() > 0.65,
      });
      addLog(
        `${id} → ${res.data.status.toUpperCase()} @ ${res.data.power_level_kw.toFixed(0)} kW`,
        res.data.status === 'queued' ? 'warn' : 'info',
      );
      fetchSessions();
    } catch {
      addLog(`Slot request failed for ${id}`, 'error');
    }
    setBusy(false);
  };

  /** Tell the backend to jump to peak-stress scenario immediately */
  const simulateStress = async () => {
    if (busy) return;
    setBusy(true);
    addLog('⚡ Injecting grid stress event...', 'warn');
    try {
      const res = await axios.post(`${API_URL}/api/grid/inject-stress`, {}, { timeout: 5000 });
      setGridStatus(res.data);
      prevGsi.current = res.data.gsi_score;
      addLog(
        `STRESS INJECTED: GSI ${res.data.gsi_score.toFixed(1)} — V2G ${res.data.v2g_enabled ? 'ACTIVE' : 'INACTIVE'}`,
        'critical',
      );
      // Refresh sessions immediately so rebalanced power shows
      fetchSessions();
    } catch {
      addLog('Stress inject failed — backend offline?', 'error');
    }
    setBusy(false);
  };

  const simulateFailure = async () => {
    if (busy) return;
    setBusy(true);
    addLog('🚨 Injecting transformer failure event...', 'critical');
    try {
      const res = await axios.post(`${API_URL}/api/grid/inject-failure`, {}, { timeout: 5000 });
      setGridStatus(res.data);
      prevGsi.current = res.data.gsi_score;
      addLog(`FAILURE MODE ON — GSI ${res.data.gsi_score.toFixed(1)}`, 'critical');
      fetchSessions();
    } catch {
      addLog('Failure inject failed — backend offline?', 'error');
    }
    setBusy(false);
  };

  const clearFailure = async () => {
    if (busy) return;
    setBusy(true);
    try {
      await axios.post(`${API_URL}/api/grid/clear-failure`, {}, { timeout: 5000 });
      addLog('✅ Transformer failure cleared', 'info');
      fetchGrid();
    } catch {
      addLog('Clear failure request failed', 'error');
    }
    setBusy(false);
  };

  const escalateP0 = async (vehicleId) => {
    try {
      // Fix BUG-B3: Correct endpoint path
      await axios.post(`${API_URL}/api/charging/slots/escalate`, { vehicle_id: vehicleId });
      addLog(`Escalated ${vehicleId} to P0 Emergency`, 'critical');
      fetchSessions();
    } catch {
      addLog(`Failed to escalate ${vehicleId}`, 'error');
    }
  };

  const setSimulationState = async (payload, label) => {
    if (busy) return;
    setBusy(true);
    try {
      const res = await axios.post(`${API_URL}/api/grid/simulation-control`, payload, { timeout: 5000 });
      addLog(`Simulation updated: ${label} (speed ${res.data.speed_multiplier}x)`, 'info');
      fetchGrid();
    } catch {
      addLog('Simulation control failed', 'error');
    }
    setBusy(false);
  };

  // ── Derived display values ────────────────────────────────────────────────

  const gsi  = gridStatus?.gsi_score ?? 0;
  const tier =
    gsi <= 30 ? { label: '🟢 GREEN',  cls: 'tier-green'  }
    : gsi <= 55 ? { label: '🟡 YELLOW', cls: 'tier-yellow' }
    : gsi <= 75 ? { label: '🟠 ORANGE', cls: 'tier-orange' }
    :             { label: '🔴 RED',    cls: 'tier-red'    };

  const scenarioLabel = SCENARIO_LABELS[gridStatus?.scenario] ?? '—';
  const chartData = historyData.map((p) => ({
    t: p.timestamp ? p.timestamp.slice(11, 19) : '--:--:--',
    gsi: p.gsi_score,
    load: p.load_percentage,
    ren: p.renewable_penetration_pct,
  }));
  const stressIntensity = Math.min(1, gsi / 100);

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="app">
      <div className="scanlines" />
      <NotificationLayer wsData={wsData} />
      <OnboardingTour />

      {/* ── Header ── */}
      <header className="header">
        <div className="header-left">
          <Link to="/" style={{ textDecoration: 'none' }}>
            <div className="logo">
              <span className="logo-sym">⚡</span>
              <span className="logo-text">GRIDCHARGE</span>
            </div>
          </Link>
          <div className="header-sub">Grid Stress-Aware EV Charging System</div>
          <div style={{ marginLeft: '2rem', display: 'flex', gap: '1rem', alignItems: 'center' }}>
            <Link to="/" className="nav-link" style={{color: '#aaa', textDecoration: 'none', fontWeight: 'bold'}}>DASHBOARD</Link>
            <Link to="/history" className="nav-link" style={{color: '#aaa', textDecoration: 'none', fontWeight: 'bold'}}>HISTORY</Link>
            <Link to="/admin" className="nav-link" style={{color: '#aaa', textDecoration: 'none', fontWeight: 'bold'}}>ADMIN</Link>
          </div>
        </div>
        <div className="header-right">
          <div className={`status-pill ${healthy ? 'pill-ok' : healthy === false ? 'pill-err' : 'pill-ok'}`}>
            <span className="pill-dot" />
            {healthy === null ? 'CONNECTING...' : healthy ? 'API ONLINE' : 'API OFFLINE'}
          </div>
          <div className="scenario-badge">{scenarioLabel}</div>
          <div className="clock">{clock}</div>
        </div>
      </header>

      <main className="main">
        <Routes>
          <Route path="/history" element={<History />} />
          <Route path="/admin" element={<Admin />} />
          <Route path="/" element={
            <>
              {/* ── Column 1 — GSI ── */}
              <section className="col-left panel-gsi">
                <div className="panel panel-gsi-inner">
          <div className="panel-header">
            <span className="panel-title">GRID STRESS INDEX</span>
            <span className={`tier-badge ${tier.cls}`}>{tier.label}</span>
          </div>

          <div className="gsi-center">
            <GSIGauge score={gsi} />
          </div>

          <div className="gsi-policy">
            <div className="policy-label">ACTIVE POLICY</div>
            <div className="policy-text">{gridStatus?.charging_policy ?? 'Waiting for data...'}</div>
          </div>

          <div className="gsi-bars">
            <Bar value={gridStatus?.load_percentage          ?? 0} label="LOAD %" />
            <Bar value={gridStatus?.renewable_penetration_pct ?? 0} label="RENEWABLE %" />
            <Bar value={gridStatus?.transformer_temp_pct      ?? 0} label="TRANSFORMER TEMP %" />
          </div>

          <div className="gsi-meta">
            <div className="meta-item">
              <span className="meta-k">MAX POWER</span>
              <span className="meta-v">{gridStatus?.max_power_kw?.toFixed(0) ?? '—'} kW</span>
            </div>
            <div className="meta-item">
              <span className="meta-k">NEW CONN.</span>
              <span className={`meta-v ${gridStatus?.allow_new_connections ? 'v-yes' : 'v-no'}`}>
                {gridStatus?.allow_new_connections ? 'ALLOWED' : 'BLOCKED'}
              </span>
            </div>
            <div className="meta-item">
              <span className="meta-k">V2G MODE</span>
              <span className={`meta-v ${gridStatus?.v2g_enabled ? 'v-yes' : 'v-no'}`}>
                {gridStatus?.v2g_enabled ? 'ACTIVE' : 'STANDBY'}
              </span>
            </div>
          </div>

                {/* Live frequency readout */}
                <div className="freq-bar">
                  <span className="freq-label">GRID FREQ</span>
                  <span className={`freq-val ${
                    Math.abs((gridStatus?.frequency_hz ?? 50) - 50) > 0.3 ? 'freq-warn' : ''
                  }`}>
                    {gridStatus?.frequency_hz?.toFixed(3) ?? '—'} Hz
                  </span>
                </div>
              </div>

              <TransformerHeatmap gridStatus={gridStatus} />
            </section>

        {/* ── Column 2 — Stats + Sessions ── */}
        <section className="col-mid">
          <div className="stats-grid">
            <StatCard label="ACTIVE SESSIONS" value={sessions.total_active} sub="charging now" accent />
            <StatCard label="QUEUED"           value={sessions.queued}       sub="waiting" />
            <StatCard label="V2G VEHICLES"     value={v2g.registered_vehicles} sub="registered" />
            <StatCard
              label="V2G CAPACITY"
              value={v2g.current_v2g_capacity_kw.toFixed(1)}
              unit="kW"
              sub="discharging"
              accent
            />
            <StatCard
              label="CARBON SAVED"
              value={(gridStatus?.carbon_saved_kg ?? 0).toFixed(1)}
              unit="kg"
              sub="renewable offset"
            />
            <StatCard
              label="GRID MODE"
              value={gridStatus?.fault_active ? 'FAULT' : 'NORMAL'}
              sub={`sim ${gridStatus?.speed_multiplier?.toFixed?.(1) ?? '1.0'}x`}
              accent={Boolean(gridStatus?.fault_active)}
            />
          </div>

          <div className="panel panel-sessions">
            <div className="panel-header">
              <span className="panel-title">ACTIVE CHARGING SESSIONS</span>
              <span className="panel-count">{sessions.total_active} ACTIVE · {sessions.queued} QUEUED</span>
            </div>
            <div className="sessions-header">
              <span>VEHICLE ID</span>
              <span>POWER</span>
              <span>UPTIME</span>
              <span>STATUS</span>
            </div>
            <div className="sessions-body">
              {sessions.sessions.length === 0 ? (
                <div className="empty-state">NO ACTIVE SESSIONS — waiting for EV arrivals</div>
              ) : (
                sessions.sessions.slice(0, 10).map((s, i) => (
                  <SessionRow
                    key={s.vehicle_id}
                    id={s.vehicle_id}
                    power={wsData.powerRamps[s.vehicle_id] || s.power_kw}
                    time={s.time_active_minutes}
                    isV2g={s.is_v2g}
                    index={i}
                    onEscalate={escalateP0}
                  />
                ))
              )}
            </div>
          </div>

          <VehicleSimulatorPanel
            onSimulationComplete={(data) => {
              addLog(
                `${data.vehicle_id} → ${data.slot_status.toUpperCase()} @ ${Number(data.allocated_power_kw).toFixed(1)} kW`,
                data.slot_status === 'queued' ? 'warn' : 'info',
              );
              fetchSessions();
            }}
          />

          <div className="panel panel-actions">
            <div className="panel-header">
              <span className="panel-title">SIMULATION CONTROLS</span>
              <span className="panel-count">LIVE BACKEND</span>
            </div>
            <div className="action-row">
              <button className="btn btn-primary" onClick={simulateEV} disabled={busy}>
                + SIMULATE EV ARRIVAL
              </button>
            </div>
            <div className="action-row" style={{ marginTop: '0.5rem' }}>
              <select 
                className="btn" 
                style={{ width: '100%', background: '#262626', color: '#fff', border: '1px solid #444', textAlign: 'left', padding: '0.5rem' }}
                onChange={(e) => {
                  const val = e.target.value;
                  if (val === 'morning_peak') simulateStress();
                  else if (val === 'transformer_failure') simulateFailure();
                  else if (val === 'solar_glut') clearFailure();
                  e.target.value = "";
                }}
                disabled={busy}
              >
                <option value="">🎯 Trigger Scenario Preset...</option>
                <option value="morning_peak">🌅 Morning Peak Rush (Stress)</option>
                <option value="transformer_failure">🚨 Transformer Failure (Critical)</option>
                <option value="solar_glut">☀️ Solar Glut (Normal/Abundant)</option>
              </select>
            </div>
            <div className="action-row action-row--small" style={{ marginTop: '1rem' }}>
              <button className="btn btn-primary" onClick={() => setSimulationState({ paused: true }, 'paused')} disabled={busy}>
                PAUSE
              </button>
              <button className="btn btn-primary" onClick={() => setSimulationState({ paused: false }, 'resumed')} disabled={busy}>
                RESUME
              </button>
              <button className="btn btn-primary" onClick={() => setSimulationState({ speed_multiplier: 2.0 }, '2x speed')} disabled={busy}>
                2X
              </button>
              <button className="btn btn-primary" onClick={() => setSimulationState({ speed_multiplier: 1.0 }, '1x speed')} disabled={busy}>
                1X
              </button>
            </div>
            <div className="external-strip">
              <span>EXT SIGNAL: {externalSignals.online ? 'LIVE' : 'OFFLINE'}</span>
              <span>TEMP {externalSignals.temperature_c ?? '--'}°C</span>
              <span>WIND {externalSignals.wind_speed_kmh ?? '--'} km/h</span>
              <span>CLOUD {externalSignals.cloud_cover_pct ?? '--'}%</span>
            </div>
          </div>

          <div className="panel panel-history">
            <div className="panel-header">
              <span className="panel-title">GRID STRESS HISTORY (REAL-TIME)</span>
              <span className="panel-count">{historyData.length} POINTS</span>
            </div>
            <div className="history-chart">
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={chartData}>
                  <CartesianGrid stroke="#1f1f1f" />
                  <XAxis dataKey="t" tick={{ fill: '#777', fontSize: 10 }} interval="preserveStartEnd" />
                  <YAxis tick={{ fill: '#777', fontSize: 10 }} domain={[0, 100]} />
                  <Tooltip contentStyle={{ background: '#080808', border: '1px solid #262626', color: '#ddd' }} />
                  <Line type="monotone" dataKey="gsi" stroke="#ffffff" strokeWidth={2} dot={false} name="GSI" />
                  <Line type="monotone" dataKey="load" stroke="#777777" strokeWidth={1.5} dot={false} name="Load %" />
                  <Line type="monotone" dataKey="ren" stroke="#aaaaaa" strokeWidth={1.5} dot={false} name="Renew %" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </section>

        {/* ── Column 3 — V2G + Tiers + Log ── */}
        <section className="col-right">
          <div className="panel panel-3d">
            <div className="panel-header">
              <span className="panel-title">3D GRID CORE</span>
              <span className="panel-count">LIVE VISUAL</span>
            </div>
            <ThreeGridScene intensity={stressIntensity} />
          </div>

          <div className="panel panel-v2g">
            <div className="panel-header">
              <span className="panel-title">V2G PROGRAM STATUS</span>
              <span className={`live-badge ${gridStatus?.v2g_enabled ? 'live-on' : 'live-off'}`}>
                {gridStatus?.v2g_enabled ? '● LIVE' : '○ STANDBY'}
              </span>
            </div>
            <div className="v2g-grid">
              <div className="v2g-item">
                <div className="v2g-val">{v2g.registered_vehicles}</div>
                <div className="v2g-key">REGISTERED</div>
              </div>
              <div className="v2g-item">
                <div className="v2g-val">{v2g.active_discharges}</div>
                <div className="v2g-key">DISCHARGING</div>
              </div>
              <div className="v2g-item">
                <div className="v2g-val">{v2g.current_v2g_capacity_kw.toFixed(1)}</div>
                <div className="v2g-key">CAPACITY kW</div>
              </div>
              <div className="v2g-item">
                <div className="v2g-val">₹{v2g.total_compensation_paid.toFixed(0)}</div>
                <div className="v2g-key">COMPENSATED</div>
              </div>
            </div>
            <div className="v2g-threshold">
              <span className="thresh-label">TRIGGER THRESHOLD</span>
              <span className="thresh-val">GSI &gt; 75</span>
            </div>
          </div>

          <V2GEarningsWidget wsData={wsData} />

          <div className="panel panel-tiers" style={{ marginTop: '1rem' }}>
            <div className="panel-header">
              <span className="panel-title">PRIORITY TIERS</span>
            </div>
            <div className="tiers-list">
              {[
                { p: 'P0', label: 'EMERGENCY',         deferral: '0 min' },
                { p: 'P1', label: 'CRITICAL BATTERY',  deferral: '5 min' },
                { p: 'P2', label: 'FLEET / COMMERCIAL', deferral: '15 min' },
                { p: 'P3', label: 'PRE-BOOKED PUBLIC',  deferral: '20 min' },
                { p: 'P4', label: 'WALK-IN',            deferral: '45 min' },
                { p: 'P5', label: 'OPPORTUNISTIC',      deferral: '∞' },
              ].map(({ p, label, deferral }) => (
                <div key={p} className="tier-row">
                  <span className="tier-p">{p}</span>
                  <span className="tier-label">{label}</span>
                  <span className="tier-defer">{deferral}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="panel panel-log">
            <div className="panel-header">
              <span className="panel-title">EVENT LOG</span>
              <span className="panel-count">{log.length} ENTRIES</span>
            </div>
            <div className="log-body">
              {log.slice(0, 16).map((e, i) => (
                <LogEntry key={i} time={e.time} msg={e.msg} type={e.type} />
              ))}
            </div>
          </div>
        </section>
        </>
      } />
      </Routes>
    </main>

      <footer className="footer">
        <span>GRIDCHARGE v1.0 — HACKATHON MVP</span>
        <span className="footer-dot">◆</span>
        <span>GSI: {gsi.toFixed(2)}</span>
        <span className="footer-dot">◆</span>
        <span>FREQ: {gridStatus?.frequency_hz?.toFixed(3) ?? '—'} Hz</span>
        <span className="footer-dot">◆</span>
        <span>SCENARIO: {scenarioLabel}</span>
        <span className="footer-dot">◆</span>
        <span>POLL: 3s</span>
      </footer>
    </div>
  );
}