import React, { useMemo, useState } from 'react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const DEFAULT_LAT = 12.9352;
const DEFAULT_LNG = 77.6245;

const randomVehicleId = () => `EV-${Math.floor(1000 + Math.random() * 9000)}`;

const defaultDepartureTime = () => {
  const dt = new Date(Date.now() + 90 * 60 * 1000);
  const local = new Date(dt.getTime() - dt.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 16);
};

function gsiBarWidth(gsi) {
  if (typeof gsi !== 'number') return '0%';
  return `${Math.max(0, Math.min(100, gsi))}%`;
}

function statusBadgeClass(status) {
  if (status === 'assigned') return 'sim-badge sim-badge--assigned';
  if (status === 'queued') return 'sim-badge sim-badge--queued';
  return 'sim-badge sim-badge--v2g';
}

export default function VehicleSimulatorPanel({ onSimulationComplete }) {
  const [isOpen, setIsOpen] = useState(true);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [form, setForm] = useState({
    vehicle_id: randomVehicleId(),
    soc_percent: 28,
    target_soc_percent: 85,
    departure_time: defaultDepartureTime(),
    user_priority: 3,
    is_v2g_capable: false,
    location_name: 'Koramangala, Bengaluru',
    lat: DEFAULT_LAT,
    lng: DEFAULT_LNG,
  });

  const socDelta = useMemo(
    () => Math.max(0, Number(form.target_soc_percent) - Number(form.soc_percent)),
    [form.soc_percent, form.target_soc_percent],
  );

  const setField = (key, value) => setForm((prev) => ({ ...prev, [key]: value }));

  const runSimulation = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const payload = {
        vehicle_id: form.vehicle_id,
        soc_percent: Number(form.soc_percent),
        target_soc_percent: Number(form.target_soc_percent),
        departure_time: new Date(form.departure_time).toISOString(),
        user_priority: Number(form.user_priority),
        is_v2g_capable: Boolean(form.is_v2g_capable),
        location: {
          lat: Number(form.lat),
          lng: Number(form.lng),
          name: form.location_name,
        },
      };

      const res = await axios.post(`${API_URL}/api/charging/simulate`, payload, { timeout: 10000 });
      setResult(res.data);
      if (onSimulationComplete) onSimulationComplete(res.data);
      setField('vehicle_id', randomVehicleId());
    } catch (err) {
      const message = err?.response?.data?.detail || 'Simulation failed. Please retry.';
      setError(typeof message === 'string' ? message : 'Simulation failed. Please retry.');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="panel panel-simulator">
      <div
        className="panel-header panel-header--clickable"
        role="button"
        tabIndex={0}
        onClick={() => setIsOpen((prev) => !prev)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            setIsOpen((prev) => !prev);
          }
        }}
      >
        <span className="panel-title">VEHICLE SIMULATOR</span>
        <span className="panel-count">{isOpen ? '▼ OPEN' : '▶ CLOSED'}</span>
      </div>

      {isOpen && (
        <>
          <form className="simulator-form" onSubmit={runSimulation}>
            <div className="sim-field">
              <label>VEHICLE ID</label>
              <input
                className="sim-input"
                type="text"
                value={form.vehicle_id}
                onChange={(e) => setField('vehicle_id', e.target.value)}
                required
              />
            </div>

            <div className="sim-field">
              <label>SOC % ({Number(form.soc_percent).toFixed(0)}%)</label>
              <input
                className="sim-slider"
                type="range"
                min="0"
                max="100"
                value={form.soc_percent}
                onChange={(e) => setField('soc_percent', Number(e.target.value))}
              />
            </div>

            <div className="sim-field">
              <label>TARGET SOC % ({Number(form.target_soc_percent).toFixed(0)}%)</label>
              <input
                className="sim-slider"
                type="range"
                min="0"
                max="100"
                value={form.target_soc_percent}
                onChange={(e) => setField('target_soc_percent', Number(e.target.value))}
              />
            </div>

            <div className="sim-field">
              <label>DEPARTURE TIME</label>
              <input
                className="sim-input"
                type="datetime-local"
                value={form.departure_time}
                onChange={(e) => setField('departure_time', e.target.value)}
                required
              />
            </div>

            <div className="sim-field">
              <label>PRIORITY TIER</label>
              <select
                className="sim-select"
                value={form.user_priority}
                onChange={(e) => setField('user_priority', Number(e.target.value))}
              >
                <option value={0}>P0 Emergency</option>
                <option value={1}>P1 Critical Battery</option>
                <option value={2}>P2 Fleet Commercial</option>
                <option value={3}>P3 Prebooked Public</option>
                <option value={4}>P4 Walk-in Public</option>
                <option value={5}>P5 Opportunistic</option>
              </select>
            </div>

            <div className="sim-field sim-field--inline">
              <label>
                <input
                  type="checkbox"
                  checked={form.is_v2g_capable}
                  onChange={(e) => setField('is_v2g_capable', e.target.checked)}
                />
                <span>V2G CAPABLE</span>
              </label>
            </div>

            <div className="sim-field">
              <label>LOCATION NAME</label>
              <input
                className="sim-input"
                type="text"
                value={form.location_name}
                onChange={(e) => setField('location_name', e.target.value)}
                required
              />
            </div>

            <div className="sim-latlng">
              <div className="sim-field">
                <label>LATITUDE</label>
                <input
                  className="sim-input"
                  type="number"
                  step="0.0001"
                  value={form.lat}
                  onChange={(e) => setField('lat', Number(e.target.value))}
                  required
                />
              </div>
              <div className="sim-field">
                <label>LONGITUDE</label>
                <input
                  className="sim-input"
                  type="number"
                  step="0.0001"
                  value={form.lng}
                  onChange={(e) => setField('lng', Number(e.target.value))}
                  required
                />
              </div>
            </div>

            <button className="btn btn-primary" type="submit" disabled={loading}>
              {loading ? 'RUNNING...' : '▶ RUN SIMULATION'}
            </button>
          </form>

          {error && (
            <div className="sim-result">
              <div className="log-entry log-entry--error">
                <span className="log-time">ERR</span>
                <span className="log-msg">{error}</span>
              </div>
            </div>
          )}

          {result && !error && (
            <div className="sim-result">
              <div className="sim-result-head">
                <div className="sim-main-val">
                  {Number(result.allocated_power_kw || 0).toFixed(1)}
                  <span> kW</span>
                </div>
                <div className="sim-main-sub">
                  {result.estimated_charge_time_minutes} MIN · ΔSOC {socDelta.toFixed(0)}%
                </div>
              </div>

              <div className="sim-result-grid">
                <div>
                  <div className="sim-k">SLOT STATUS</div>
                  <div className={statusBadgeClass(result.slot_status)}>{result.slot_status}</div>
                </div>
                <div>
                  <div className="sim-k">EST COST</div>
                  <div className="sim-v">₹{Number(result.estimated_cost_inr || 0).toFixed(2)}</div>
                </div>
                <div>
                  <div className="sim-k">CARBON OFFSET</div>
                  <div className="sim-v">{Number(result.carbon_offset_kg || 0).toFixed(3)} kg</div>
                </div>
                <div>
                  <div className="sim-k">OPTIMAL START</div>
                  <div className="sim-v">{new Date(result.optimal_start_window).toLocaleString()}</div>
                </div>
              </div>

              <div className="sim-recommendation">{result.recommendation}</div>

              <div className="sim-gsi">
                <div className="sim-gsi-head">
                  <span>GSI @ REQUEST</span>
                  <span>{Number(result.gsi_at_request || 0).toFixed(1)}</span>
                </div>
                <div className="bar-track">
                  <div className="bar-fill" style={{ width: gsiBarWidth(result.gsi_at_request) }} />
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
