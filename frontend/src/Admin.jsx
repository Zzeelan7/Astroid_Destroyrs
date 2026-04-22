import React, { useState } from 'react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export default function Admin() {
  const [msg, setMsg] = useState('');

  const clearDB = async () => {
    // Mock functionality since there's no endpoint yet
    setMsg('DB Clear mock executed (no backend endpoint yet)');
  };

  const forceV2g = async () => {
    try {
      await axios.post(`${API_URL}/api/grid/inject-stress`);
      setMsg('Forced grid stress (V2G should trigger if capable EVs exist)');
    } catch (e) {
      setMsg('Error forcing stress');
    }
  };

  return (
    <div style={{ padding: '2rem', color: '#fff' }}>
      <h1>Admin Control Panel</h1>
      
      <div style={{ marginTop: '2rem', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
        <div className="panel" style={{ padding: '1rem', width: '300px' }}>
          <h3>Manual Overrides</h3>
          <button className="btn btn-danger" onClick={forceV2g} style={{ marginTop: '1rem', width: '100%' }}>
            Force GSI Stress (>75)
          </button>
          <button className="btn btn-primary" onClick={clearDB} style={{ marginTop: '1rem', width: '100%' }}>
            Clear DB / Sessions
          </button>
        </div>
        
        <div className="panel" style={{ padding: '1rem', width: '300px' }}>
          <h3>System Status</h3>
          <p>WebSocket Connections: <span style={{ color: '#4ade80' }}>ACTIVE</span></p>
          <p>Database: <span style={{ color: '#4ade80' }}>PostgreSQL ONLINE</span></p>
          <p>MQTT Broker: <span style={{ color: '#4ade80' }}>Mosquitto ONLINE</span></p>
        </div>
      </div>
      
      {msg && <div style={{ marginTop: '1rem', padding: '1rem', background: '#333', borderRadius: '4px' }}>{msg}</div>}
    </div>
  );
}
