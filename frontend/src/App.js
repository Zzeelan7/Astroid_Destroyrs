import React, { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';

// In Docker the frontend container calls the API via the host machine's port 8000
// In local dev it's also localhost:8000
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// ─── Utility ────────────────────────────────────────────────────────────────
const pad = (n) => String(n).padStart(2, '0');
const ts = () => {
  const d = new Date();
  return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
};

// ─── GSI Gauge ──────────────────────────────────────────────────────────────
function GSIGauge({ score }) {
  const r = 80;
  const circ = 2 * Math.PI * r;
  const dash = (score / 100) * circ;
  const gap = circ - dash;

  const tier =
    score <= 30 ? { label: 'LOW STRESS' }
    : score <= 55 ? { label: 'MODERATE' }
    : score <= 75 ? { label: 'HIGH STRESS' }
    : { label: 'CRITICAL' };

  return (
    <div className="gauge-wrapper">
      <svg width="200" height="200" viewBox="0 0 200 200">
        <circle cx="100" cy="100" r={r} fill="none" stroke="#1a1a1a" strokeWidth="12" />
        {[0, 25, 50, 75, 100].map((v) => {
          const angle = (v / 100) * 360 - 90;
          const rad = (angle * Math.PI) / 180;
          const x1 = 100 + (r - 18) * Math.cos(rad);
          const y1 = 100 + (r - 18) * Math.sin(rad);
          const x2 = 100 + (r + 5) * Math.cos(rad);
          const y2 = 100 + (r + 5) * Math.sin(rad);
          return <line key={v} x1={x1} y1={y1} x2={x2} y2={y2} stroke="#333" strokeWidth="1.5" />;
        })}
        <circle
          cx="100" cy="100" r={r}
          fill="none"
          stroke="white"
          strokeWidth="12"
          strokeDasharray={`${dash} ${gap}`}
          strokeDashoffset={circ * 0.25}
          strokeLinecap="butt"
          style={{ transition: 'stroke-dasharray 0.8s cubic-bezier(0.4,0,0.2,1)' }}
        />
        <text x="100" y="92" textAnchor="middle" fill="white" fontSize="38" fontFamily="'IBM Plex Mono', monospace" fontWeight="700">
          {score.toFixed(0)}
        </text>
        <text x="100" y="112" textAnchor="middle" fill="#666" fontSize="11" fontFamily="'IBM Plex Mono', monospace" letterSpacing="3">
          / 100
        </text>
        <text x="100" y="134" textAnchor="middle" fill="#aaa" fontSize="10" fontFamily="'IBM Plex Mono', monospace" letterSpacing="2">
          {tier.label}
        </text>
      </svg>
    </div>
  );
}

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

function SessionRow({ id, power, time, index }) {
  return (
    <div className="session-row" style={{ animationDelay: `${index * 60}ms` }}>
      <span className="session-id">{id}</span>
      <span className="session-power">{power.toFixed(1)} <span style={{ color: '#555', fontSize: '11px' }}>kW</span></span>
      <span className="session-time">{time}m</span>
      <span className="session-dot">●</span>
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

export default function App() {
  const [gridStatus, setGridStatus] = useState(null);
  const [sessions, setSessions] = useState({ total_active: 0, queued: 0, sessions: [] });
  const [v2g, setV2g] = useState({ registered_vehicles: 0, active_discharges: 0, current_v2g_capacity_kw: 0, total_compensation_paid: 0 });
  const [log, setLog] = useState([]);
  const [tick, setTick] = useState(0);
  const [healthy, setHealthy] = useState(null);
  const logRef = useRef([]);

  const addLog = useCallback((msg, type = 'info') => {
    const entry = { time: ts(), msg, type };
    logRef.current = [entry, ...logRef.current].slice(0, 40);
    setLog([...logRef.current]);
  }, []);

  const fetchHealth = useCallback(async () => {
    try {
      await axios.get(`${API_URL}/api/health/`, { timeout: 5000 });
      setHealthy(true);
    } catch {
      setHealthy(false);
    }
  }, []);

  const fetchGrid = useCallback(async () => {
    try {
      const load = 25 + Math.random() * 70;
      const freq = 49.5 + Math.random() * 1.0;
      const temp = 30 + Math.random() * 55;
      const ren = 15 + Math.random() * 65;

      const res = await axios.post(`${API_URL}/api/grid/status`, {
        load_percentage: load,
        frequency_hz: freq,
        transformer_temp_pct: temp,
        renewable_penetration_pct: ren,
      }, { timeout: 5000 });

      const prev = gridStatus?.gsi_score;
      setGridStatus({ ...res.data, load, freq, temp, ren });

      if (prev !== undefined) {
        const diff = res.data.gsi_score - prev;
        if (Math.abs(diff) > 8) {
          addLog(
            `GSI ${diff > 0 ? '▲' : '▼'} ${Math.abs(diff).toFixed(1)} → ${res.data.gsi_score.toFixed(1)} — ${res.data.status}`,
            res.data.gsi_score > 75 ? 'critical' : res.data.gsi_score > 55 ? 'warn' : 'info'
          );
        }
      }
    } catch (e) {
      addLog('Grid API unreachable — check backend is running', 'error');
    }
  }, [gridStatus, addLog]);

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

  useEffect(() => {
    fetchHealth();
    fetchGrid();
    fetchSessions();
    fetchV2G();
    addLog('GridCharge dashboard initialized', 'info');
    addLog(`Connecting to API at ${API_URL}...`, 'info');
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const t = setInterval(() => {
      setTick(p => p + 1);
      fetchGrid();
      fetchSessions();
      fetchV2G();
      if (tick % 3 === 0) fetchHealth();
    }, 4000);
    return () => clearInterval(t);
  }, [tick, fetchGrid, fetchSessions, fetchV2G, fetchHealth]);

  const gsi = gridStatus?.gsi_score ?? 0;

  const tier =
    gsi <= 30 ? { label: '🟢 GREEN', cls: 'tier-green' }
    : gsi <= 55 ? { label: '🟡 YELLOW', cls: 'tier-yellow' }
    : gsi <= 75 ? { label: '🟠 ORANGE', cls: 'tier-orange' }
    : { label: '🔴 RED', cls: 'tier-red' };

  const simulateEV = async () => {
    const id = `EV-${String(Math.floor(Math.random() * 9000) + 1000)}`;
    const soc = Math.floor(Math.random() * 60) + 10;
    const dep = new Date(Date.now() + 90 * 60000).toISOString();
    try {
      const res = await axios.post(`${API_URL}/api/charging/request-slot`, {
        vehicle_id: id,
        soc_percent: soc,
        target_soc_percent: Math.min(100, soc + 40),
        departure_time: dep,
        user_priority: Math.floor(Math.random() * 4) + 1,
        is_v2g_capable: Math.random() > 0.6,
      });
      addLog(`${id} → ${res.data.status.toUpperCase()} @ ${res.data.power_level_kw.toFixed(0)} kW`, 'info');
      fetchSessions();
    } catch {
      addLog(`Slot request failed for ${id}`, 'error');
    }
  };

  const simulateStress = async () => {
    addLog('⚡ Injecting grid stress event...', 'warn');
    try {
      const res = await axios.post(`${API_URL}/api/grid/status`, {
        load_percentage: 90 + Math.random() * 9,
        frequency_hz: 49.3 + Math.random() * 0.3,
        transformer_temp_pct: 82 + Math.random() * 12,
        renewable_penetration_pct: 5 + Math.random() * 10,
      });
      setGridStatus(s => ({ ...s, ...res.data }));
      addLog(`STRESS EVENT: GSI ${res.data.gsi_score.toFixed(1)} — V2G ${res.data.v2g_enabled ? 'ACTIVE' : 'INACTIVE'}`, 'critical');
    } catch {
      addLog('Stress inject failed — backend offline?', 'error');
    }
  };

  return (
    <div className="app">
      <div className="scanlines" />

      <header className="header">
        <div className="header-left">
          <div className="logo">
            <span className="logo-sym">⚡</span>
            <span className="logo-text">GRIDCHARGE</span>
          </div>
          <div className="header-sub">Grid Stress-Aware EV Charging System</div>
        </div>
        <div className="header-right">
          <div className={`status-pill ${healthy ? 'pill-ok' : healthy === false ? 'pill-err' : 'pill-ok'}`}>
            <span className="pill-dot" />
            {healthy === null ? 'CONNECTING...' : healthy ? 'API ONLINE' : 'API OFFLINE'}
          </div>
          <div className="clock">{ts()}</div>
        </div>
      </header>

      <main className="main">
        {/* Column 1 — GSI */}
        <section className="panel panel-gsi">
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
            <Bar value={gridStatus?.load ?? 0} label="LOAD %" />
            <Bar value={gridStatus?.ren ?? 0} label="RENEWABLE %" />
            <Bar value={gridStatus?.temp ?? 0} label="TRANSFORMER TEMP %" />
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
        </section>

        {/* Column 2 — Stats + Sessions */}
        <section className="col-mid">
          <div className="stats-grid">
            <StatCard label="ACTIVE SESSIONS" value={sessions.total_active} sub="charging now" accent />
            <StatCard label="QUEUED" value={sessions.queued} sub="waiting" />
            <StatCard label="V2G VEHICLES" value={v2g.registered_vehicles} sub="registered" />
            <StatCard label="V2G CAPACITY" value={v2g.current_v2g_capacity_kw.toFixed(1)} unit="kW" sub="discharging" accent />
          </div>

          <div className="panel panel-sessions">
            <div className="panel-header">
              <span className="panel-title">ACTIVE CHARGING SESSIONS</span>
              <span className="panel-count">{sessions.total_active} ACTIVE</span>
            </div>
            <div className="sessions-header">
              <span>VEHICLE ID</span>
              <span>POWER</span>
              <span>UPTIME</span>
              <span>STATUS</span>
            </div>
            <div className="sessions-body">
              {sessions.sessions.length === 0 ? (
                <div className="empty-state">NO ACTIVE SESSIONS</div>
              ) : (
                sessions.sessions.slice(0, 8).map((s, i) => (
                  <SessionRow key={s.vehicle_id} id={s.vehicle_id} power={s.power_kw} time={s.time_active_minutes} index={i} />
                ))
              )}
            </div>
          </div>

          <div className="panel panel-actions">
            <div className="panel-header">
              <span className="panel-title">SIMULATION CONTROLS</span>
            </div>
            <div className="action-row">
              <button className="btn btn-primary" onClick={simulateEV}>
                + SIMULATE EV ARRIVAL
              </button>
              <button className="btn btn-danger" onClick={simulateStress}>
                ⚡ INJECT STRESS EVENT
              </button>
            </div>
          </div>
        </section>

        {/* Column 3 — V2G + Log */}
        <section className="col-right">
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

          <div className="panel panel-tiers">
            <div className="panel-header">
              <span className="panel-title">PRIORITY TIERS</span>
            </div>
            <div className="tiers-list">
              {[
                { p: 'P0', label: 'EMERGENCY', deferral: '0 min' },
                { p: 'P1', label: 'CRITICAL BATTERY', deferral: '5 min' },
                { p: 'P2', label: 'FLEET / COMMERCIAL', deferral: '15 min' },
                { p: 'P3', label: 'PRE-BOOKED PUBLIC', deferral: '20 min' },
                { p: 'P4', label: 'WALK-IN', deferral: '45 min' },
                { p: 'P5', label: 'OPPORTUNISTIC', deferral: '∞' },
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
              {log.slice(0, 14).map((e, i) => (
                <LogEntry key={i} time={e.time} msg={e.msg} type={e.type} />
              ))}
            </div>
          </div>
        </section>
      </main>

      <footer className="footer">
        <span>GRIDCHARGE v1.0 — HACKATHON MVP</span>
        <span className="footer-dot">◆</span>
        <span>GSI: {gsi.toFixed(2)}</span>
        <span className="footer-dot">◆</span>
        <span>FREQ: {gridStatus?.freq?.toFixed(2) ?? '—'} Hz</span>
        <span className="footer-dot">◆</span>
        <span>REFRESH: 4s</span>
      </footer>
    </div>
  );
}
