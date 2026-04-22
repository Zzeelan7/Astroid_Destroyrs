import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export default function History() {
  const [history, setHistory] = useState([]);

  useEffect(() => {
    // We reuse the /api/grid/history endpoint but expand to sessions if available
    axios.get(`${API_URL}/api/grid/history?limit=100`)
      .then(res => setHistory(res.data.points || []))
      .catch(err => console.error(err));
  }, []);

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
    a.setAttribute('download', 'grid_history.csv');
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  return (
    <div style={{ padding: '2rem', color: '#fff' }}>
      <h1>Session History</h1>
      <button className="btn btn-primary" onClick={exportCSV} style={{ marginBottom: '1rem' }}>
        Export CSV
      </button>
      <table style={{ width: '100%', textAlign: 'left', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ borderBottom: '1px solid #333' }}>
            <th>Time</th>
            <th>GSI Score</th>
            <th>Load %</th>
            <th>Renewable %</th>
            <th>Transformer %</th>
          </tr>
        </thead>
        <tbody>
          {history.map((row, i) => (
            <tr key={i} style={{ borderBottom: '1px solid #1a1a1a' }}>
              <td style={{ padding: '0.5rem 0' }}>{row.timestamp.substring(11, 19)}</td>
              <td>{row.gsi_score.toFixed(1)}</td>
              <td>{row.load_percentage.toFixed(1)}</td>
              <td>{row.renewable_penetration_pct.toFixed(1)}</td>
              <td>{row.transformer_temp_pct.toFixed(1)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
