import React, { useState } from 'react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export default function Admin() {
  const [msg, setMsg] = useState('');
  const [loading, setLoading] = useState(false);

  const clearDB = async () => {
    // FEAT-3: Implement Purge DB
    if (!window.confirm("Are you sure you want to purge all session data? This cannot be undone.")) return;
    
    setLoading(true);
    try {
      const res = await axios.post(`${API_URL}/api/health/purge-db`);
      setMsg(res.data.message || 'Database purged successfully');
    } catch (e) {
      setMsg('Error purging database: ' + (e.response?.data?.message || e.message));
    }
    setLoading(false);
  };

  const forceV2g = async () => {
    setLoading(true);
    try {
      await axios.post(`${API_URL}/api/grid/inject-stress`);
      setMsg('Forced grid stress (V2G should trigger if capable EVs exist)');
    } catch (e) {
      setMsg('Error forcing stress');
    }
    setLoading(false);
  };

  return (
    <div style={{ padding: '2rem', color: '#fff' }}>
      <h1>Admin Control Panel</h1>
      
      <div style={{ marginTop: '2rem', display: 'flex', gap: '1.5rem', flexWrap: 'wrap' }}>
        <div className="panel" style={{ padding: '1.5rem', width: '350px', border: '1px solid #333' }}>
          <h3 style={{ borderBottom: '1px solid #333', paddingBottom: '0.5rem', marginBottom: '1rem' }}>Manual Overrides</h3>
          <button 
            className="btn btn-danger" 
            onClick={forceV2g} 
            disabled={loading}
            style={{ marginTop: '0.5rem', width: '100%', padding: '0.75rem', fontWeight: 'bold' }}
          >
            {loading ? 'PROCESSING...' : 'Force GSI Stress (>75)'}
          </button>
          <button 
            className="btn" 
            onClick={clearDB} 
            disabled={loading}
            style={{ 
              marginTop: '1rem', 
              width: '100%', 
              padding: '0.75rem', 
              background: '#444', 
              color: '#fff', 
              fontWeight: 'bold',
              border: '1px solid #666'
            }}
          >
            {loading ? 'PROCESSING...' : '🔥 Purge DB / Clear All Sessions'}
          </button>
        </div>
        
        <div className="panel" style={{ padding: '1.5rem', width: '350px', border: '1px solid #333' }}>
          <h3 style={{ borderBottom: '1px solid #333', paddingBottom: '0.5rem', marginBottom: '1rem' }}>System Infrastructure</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>WebSocket Relay</span>
              <span style={{ color: '#4ade80', fontWeight: 'bold' }}>● ACTIVE</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>PostgreSQL Cluster</span>
              <span style={{ color: '#4ade80', fontWeight: 'bold' }}>● ONLINE</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>MQTT Broker (Mosquitto)</span>
              <span style={{ color: '#4ade80', fontWeight: 'bold' }}>● ONLINE</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Simulation Engine</span>
              <span style={{ color: '#3b82f6', fontWeight: 'bold' }}>● RUNNING</span>
            </div>
          </div>
        </div>
      </div>
      
      {msg && (
        <div style={{ 
          marginTop: '2rem', 
          padding: '1rem', 
          background: msg.includes('Error') ? '#450a0a' : '#064e3b', 
          border: `1px solid ${msg.includes('Error') ? '#ef4444' : '#10b981'}`,
          borderRadius: '4px',
          color: '#fff'
        }}>
          {msg}
        </div>
      )}
    </div>
  );
}
