import React, { useEffect } from 'react';
import { Toaster, toast } from 'react-hot-toast';

export default function NotificationLayer({ wsData }) {
  useEffect(() => {
    if (wsData.events.length > 0) {
      const latest = wsData.events[0];
      if (latest.type === 'GSI_THRESHOLD_CROSSED') {
        if (latest.new_status === 'Red') {
          toast.error(`Grid Stress Alert! GSI crossed ${latest.gsi_score.toFixed(1)}. Initiating V2G Discharge.`, {
            style: { background: '#dc2626', color: '#fff' }
          });
        } else if (latest.new_status === 'Green' && latest.old_status !== 'Green') {
          toast.success(`Grid Stress Resolved. GSI: ${latest.gsi_score.toFixed(1)}`, {
            style: { background: '#16a34a', color: '#fff' }
          });
        }
      } else if (latest.type === 'POWER_RAMP') {
        toast(`Power Ramp Up: Session ${latest.session_id.substring(0,8)} restored to ${latest.new_power_kw.toFixed(1)} kW`, {
          icon: '⚡',
          style: { background: '#3b82f6', color: '#fff' }
        });
      }
    }
  }, [wsData.events]);

  return <Toaster position="top-right" />;
}
