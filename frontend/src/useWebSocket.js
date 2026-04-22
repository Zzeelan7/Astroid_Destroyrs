import { useState, useEffect, useRef } from 'react';

const WS_URL = (process.env.REACT_APP_API_URL || 'http://localhost:8000').replace(/^http/, 'ws');

export function useWebSocket() {
  const [wsData, setWsData] = useState({
    events: [],
    earningsBySession: {}, // session_id -> { energy_discharged_kwh, compensation_inr, total_paid }
    powerRamps: {}, // session_id -> new_power_kw
    gsiThresholds: null // { old_status, new_status, gsi_score }
  });
  
  const ws = useRef(null);

  useEffect(() => {
    let reconnectTimeout;
    
    function connect() {
      ws.current = new WebSocket(`${WS_URL}/api/ws`);
      
      ws.current.onopen = () => {
        console.log('WS connected');
      };

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          setWsData(prev => {
            const newState = { ...prev };
            newState.events = [data, ...prev.events].slice(0, 50); // keep last 50 events
            
            if (data.type === 'V2G_EARNINGS_UPDATE') {
              newState.earningsBySession = {
                ...prev.earningsBySession,
                [data.session_id]: {
                  energy_discharged_kwh: data.energy_discharged_kwh,
                  compensation_inr: data.compensation_inr,
                  total_paid: data.total_paid
                }
              };
            } else if (data.type === 'POWER_RAMP') {
              newState.powerRamps = {
                ...prev.powerRamps,
                [data.session_id]: data.new_power_kw
              };
            } else if (data.type === 'GSI_THRESHOLD_CROSSED') {
              newState.gsiThresholds = data;
            }
            
            return newState;
          });
        } catch (e) {
          console.error("WS parse error", e);
        }
      };

      ws.current.onclose = () => {
        console.log('WS disconnected, reconnecting...');
        reconnectTimeout = setTimeout(connect, 3000);
      };
      
      ws.current.onerror = (err) => {
        console.error('WS error', err);
        ws.current.close();
      };
    }

    connect();

    return () => {
      clearTimeout(reconnectTimeout);
      if (ws.current) {
        ws.current.onclose = null;
        ws.current.close();
      }
    };
  }, []);

  return wsData;
}
