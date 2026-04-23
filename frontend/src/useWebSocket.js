import { useState, useEffect, useRef } from 'react';

// Fix BUG-F7: Handle potential trailing slash in API_URL
const BASE_URL = (process.env.REACT_APP_API_URL || 'http://localhost:8000').replace(/\/$/, '');
const WS_URL = BASE_URL.replace(/^http/, 'ws');

export function useWebSocket() {
  const [wsData, setWsData] = useState({
    events: [],
    earningsBySession: {}, // session_id -> { energy_discharged_kwh, compensation_inr, total_paid }
    powerRamps: {}, // session_id -> new_power_kw
    gsiThresholds: null // { old_status, new_status, gsi_score }
  });
  
  const ws = useRef(null);
  // FEAT-4: Exponential backoff
  const reconnectAttempts = useRef(0);
  const maxDelay = 30000;

  useEffect(() => {
    let reconnectTimeout;
    
    function connect() {
      // Fix BUG-F7: Ensure clean URL joining
      ws.current = new WebSocket(`${WS_URL}/api/ws`);
      
      ws.current.onopen = () => {
        console.log('WS connected');
        reconnectAttempts.current = 0; // Reset on success
      };

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          setWsData(prev => {
            const newState = { ...prev };
            // Ensure only latest 50 events are kept (FEAT-4)
            newState.events = [data, ...prev.events].slice(0, 50);
            
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
        // FEAT-4: Exponential backoff
        const delay = Math.min(maxDelay, 1000 * Math.pow(2, reconnectAttempts.current));
        console.log(`WS disconnected, reconnecting in ${delay}ms...`);
        reconnectTimeout = setTimeout(() => {
          reconnectAttempts.current++;
          connect();
        }, delay);
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
        ws.current.onclose = null; // Prevent reconnect loop on unmount
        ws.current.close();
      }
    };
  }, []);

  return wsData;
}
