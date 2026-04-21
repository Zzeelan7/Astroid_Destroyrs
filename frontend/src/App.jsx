import React, { useState, useEffect } from 'react';
import axios from 'axios';

function App() {
  const [gridStatus, setGridStatus] = useState(null);
  const [chargingSessions, setChargingSessions] = useState([]);
  const [gsiScore, setGsiScore] = useState(0);

  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  useEffect(() => {
    fetchGridStatus();
    const interval = setInterval(fetchGridStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchGridStatus = async () => {
    try {
      const response = await axios.post(`${API_URL}/api/grid/status`, {
        load_percentage: Math.random() * 100,
        frequency_hz: 50 + (Math.random() - 0.5) * 0.5,
        transformer_temp_pct: 40 + Math.random() * 40,
        renewable_penetration_pct: 30 + Math.random() * 50,
      });
      setGridStatus(response.data);
      setGsiScore(response.data.gsi_score);
    } catch (error) {
      console.error('Error fetching grid status:', error);
    }
  };

  const getStatusColor = () => {
    if (gsiScore <= 30) return 'bg-green-100 border-green-500';
    if (gsiScore <= 55) return 'bg-yellow-100 border-yellow-500';
    if (gsiScore <= 75) return 'bg-orange-100 border-orange-500';
    return 'bg-red-100 border-red-500';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-5xl font-bold mb-2">⚡ GridCharge</h1>
          <p className="text-xl text-gray-400">Grid Stress-Aware EV Charging Slot Allocation</p>
        </div>

        {/* Grid Status */}
        {gridStatus && (
          <div className={`mb-8 p-6 rounded-lg border-4 ${getStatusColor()}`}>
            <div className="flex justify-between items-start">
              <div>
                <h2 className="text-2xl font-bold mb-2">{gridStatus.status}</h2>
                <p className="text-lg mb-4">{gridStatus.charging_policy}</p>
                <div className="space-y-2 text-sm">
                  <p>GSI Score: <strong>{gridStatus.gsi_score.toFixed(1)}/100</strong></p>
                  <p>Max Power: <strong>{gridStatus.max_power_kw.toFixed(0)} kW</strong></p>
                  <p>V2G Enabled: <strong>{gridStatus.v2g_enabled ? '✅ Yes' : '❌ No'}</strong></p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-blue-600 p-4 rounded-lg">
            <p className="text-gray-300 text-sm">Active Sessions</p>
            <p className="text-3xl font-bold">--</p>
          </div>
          <div className="bg-purple-600 p-4 rounded-lg">
            <p className="text-gray-300 text-sm">Queued Vehicles</p>
            <p className="text-3xl font-bold">--</p>
          </div>
          <div className="bg-green-600 p-4 rounded-lg">
            <p className="text-gray-300 text-sm">V2G Capacity</p>
            <p className="text-3xl font-bold">-- kW</p>
          </div>
          <div className="bg-amber-600 p-4 rounded-lg">
            <p className="text-gray-300 text-sm">Renewable %</p>
            <p className="text-3xl font-bold">--</p>
          </div>
        </div>

        {/* Coming Soon */}
        <div className="bg-slate-700 p-6 rounded-lg">
          <h3 className="text-xl font-bold mb-4">🚀 Coming Soon</h3>
          <ul className="space-y-2 text-gray-300">
            <li>✓ Real-time charging sessions dashboard</li>
            <li>✓ Grid stress visualization with Recharts</li>
            <li>✓ V2G participant status</li>
            <li>✓ Slot allocation queue preview</li>
            <li>✓ Renewable energy tracking</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default App;
