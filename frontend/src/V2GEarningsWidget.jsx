import React from 'react';
import { LineChart, Line, ResponsiveContainer, YAxis } from 'recharts';

export default function V2GEarningsWidget({ wsData }) {
  // Aggregate data from wsData.earningsBySession
  const sessions = Object.values(wsData.earningsBySession);
  
  // Total compensated so far
  const totalCompensated = sessions.length > 0 ? sessions[0].total_paid : 0;
  
  // Create a mock sparkline for earnings over the last 10 minutes based on events
  const earningsEvents = wsData.events.filter(e => e.type === 'V2G_EARNINGS_UPDATE').reverse();
  const sparklineData = earningsEvents.map((e, i) => ({ i, val: e.total_paid }));

  if (sparklineData.length === 0) {
    sparklineData.push({ i: 0, val: totalCompensated });
  }

  return (
    <div className="panel panel-v2g-earnings" style={{ marginTop: '1rem', border: '1px solid #4ade80' }}>
      <div className="panel-header">
        <span className="panel-title" style={{ color: '#4ade80' }}>⚡ LIVE V2G EARNINGS</span>
        <span className="live-badge live-on">● WS CONNECTED</span>
      </div>
      <div className="v2g-earnings-content" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '1rem' }}>
        <div className="earnings-main">
          <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: '#fff' }}>
            ₹{totalCompensated.toFixed(2)}
          </div>
          <div style={{ color: '#888', fontSize: '0.9rem' }}>TOTAL COMPENSATED</div>
        </div>
        
        <div className="earnings-sparkline" style={{ width: '150px', height: '60px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={sparklineData}>
              <YAxis domain={['dataMin', 'dataMax']} hide />
              <Line type="monotone" dataKey="val" stroke="#4ade80" strokeWidth={2} dot={false} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
