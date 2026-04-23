import React, { useMemo } from 'react';

export default function TransformerHeatmap({ gridStatus }) {
  const baseTemp = gridStatus?.transformer_temp_pct || 50;
  
  // Fix BUG-F5: Stabilize heatmap with useMemo
  const transformers = useMemo(() => {
    return Array.from({ length: 16 }).map((_, i) => {
      // Add deterministic noise based on index to prevent flickering
      let temp = baseTemp + (Math.sin(i * 1.5) * 10);
      temp = Math.max(0, Math.min(100, temp));
      
      let color = '#22c55e'; // green
      if (temp > 85) color = '#ef4444'; // red
      else if (temp > 65) color = '#eab308'; // yellow
      else if (temp > 50) color = '#3b82f6'; // blue
      
      return { id: `TX-${100+i}`, temp, color };
    });
  }, [baseTemp]);

  return (
    <div className="panel panel-heatmap" style={{ marginTop: '1rem' }}>
      <div className="panel-header">
        <span className="panel-title">TRANSFORMER HEALTH</span>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '4px', padding: '1rem' }}>
        {transformers.map(tx => (
          <div key={tx.id} style={{
            background: tx.color,
            padding: '10px 5px',
            textAlign: 'center',
            borderRadius: '4px',
            color: '#fff',
            fontSize: '0.8rem',
            fontWeight: 'bold',
            opacity: tx.temp / 100 + 0.2,
            transition: 'background 0.5s ease, opacity 0.5s ease'
          }}>
            {tx.id}
            <div style={{ fontSize: '0.7rem', opacity: 0.8 }}>{tx.temp.toFixed(0)}%</div>
          </div>
        ))}
      </div>
    </div>
  );
}
