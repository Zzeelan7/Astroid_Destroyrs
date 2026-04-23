import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export default function History() {
  const [history, setHistory] = useState([]);
  // FEAT-2: Limit toggle
  const [limit, setLimit] = useState(150);

  useEffect(() => {
    axios.get(`${API_URL}/api/grid/history?limit=${limit}`)
      .then(res => setHistory(res.data.points || []))
      .catch(err => console.error(err));
  }, [limit]);

  const exportCSV = () => {
    const header = "timestamp,gsi_score,load_percentage,renewable_pct,transformer_temp\n";
    const rows = history.map(row => 
      `${row.timestamp},${row.gsi_score.toFixed(2)},${row.load_percentage.toFixed(2)},${row.renewable_penetration_pct.toFixed(2)},${row.transformer_temp_pct.toFixed(2)}`
    ).join("\n");
    
    const blob = new Blob([header + rows], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.setAttribute('hidden', '');
    a.setAttribute('href', url);
    a.setAttribute('download', `grid_history_${limit}_pts.csv`);
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  return (
    <div style={{ padding: '2rem', color: '#fff' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1>Session History</h1>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <span style={{ color: '#888', fontSize: '0.9rem' }}>SHOW LAST:</span>
          {[50, 150, 500].map(val => (
            <button 
              key={val}
              className={`btn btn-sm ${limit === val ? 'btn-primary' : ''}`}
              style={{ minWidth: '60px', background: limit === val ? '#3b82f6' : '#262626' }}
              onClick={() => setLimit(val)}
            >
              {val}
            </button>
          ))}
          <button className="btn btn-primary" onClick={exportCSV}>
            Export CSV
          </button>
        </div>
      </div>

      <div style={{ background: '#0a0a0a', padding: '1rem', borderRadius: '8px', border: '1px solid #222' }}>
        <table style={{ width: '100%', textAlign: 'left', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #333', color: '#888', textTransform: 'uppercase', fontSize: '0.8rem' }}>
              <th style={{ padding: '1rem 0' }}>Time</th>
              <th>GSI Score</th>
              <th>Load %</th>
              <th>Renewable %</th>
              <th>Transformer %</th>
            </tr>
          </thead>
          <tbody>
            {history.length === 0 ? (
              <tr><td colSpan="5" style={{ textAlign: 'center', padding: '2rem', color: '#444' }}>NO HISTORY DATA AVAILABLE</td></tr>
            ) : (
              history.map((row, i) => (
                <tr key={i} style={{ borderBottom: '1px solid #1a1a1a', fontSize: '0.9rem' }}>
                  <td style={{ padding: '0.75rem 0' }}>{row.timestamp ? row.timestamp.substring(11, 19) : '—'}</td>
                  <td style={{ color: row.gsi_score > 75 ? '#ef4444' : row.gsi_score > 40 ? '#eab308' : '#22c55e' }}>
                    {row.gsi_score.toFixed(1)}
                  </td>
                  <td>{row.load_percentage.toFixed(1)}%</td>
                  <td>{row.renewable_penetration_pct.toFixed(1)}%</td>
                  <td>{row.transformer_temp_pct.toFixed(1)}%</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
