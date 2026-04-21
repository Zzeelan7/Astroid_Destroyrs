"""
Grid Stress Index (GSI) Engine
Computes real-time grid stress on 0-100 scale based on:
- Grid load percentage
- Frequency deviation
- Transformer temperature
- Renewable energy penetration
"""
from typing import Optional
from datetime import datetime
from dataclasses import dataclass
import numpy as np


@dataclass
class GridMetrics:
    """Real-time grid metrics from DSO telemetry"""
    timestamp: datetime
    load_percentage: float  # 0-100, % of grid capacity
    frequency_hz: float    # nominal 50 or 60 Hz
    transformer_temp_pct: float  # 0-100, % of rated thermal
    renewable_penetration_pct: float  # 0-100, % of generation from renewables


@dataclass
class GridStressLevel:
    """GSI result with policy tier"""
    gsi_score: float  # 0-100
    status: str  # "🟢 Green", "🟡 Yellow", "🟠 Orange", "🔴 Red"
    charging_policy: str  # policy description
    max_power_kw: float  # max allowed power for new EVs
    allow_new_connections: bool
    v2g_enabled: bool


class GSIEngine:
    """Grid Stress Index calculation engine"""
    
    NOMINAL_FREQUENCY_HZ = 50.0  # Europe standard; 60 for US
    FREQUENCY_TOLERANCE_HZ = 0.2
    
    def __init__(self, nominal_frequency: float = 50.0):
        self.nominal_frequency = nominal_frequency
    
    def compute_gsi(self, metrics: GridMetrics) -> GridStressLevel:
        """
        Compute GSI using weighted formula:
        GSI = 0.40×(Load%) + 0.30×(Freq Dev Index) 
            + 0.20×(Transformer Temp Index) - 0.10×(Renewable%)
        
        Args:
            metrics: GridMetrics object with telemetry
            
        Returns:
            GridStressLevel with policy tier
        """
        # Load component (0.40 weight)
        load_component = metrics.load_percentage * 0.40
        
        # Frequency deviation (0.30 weight)
        freq_deviation_hz = abs(metrics.frequency_hz - self.nominal_frequency)
        freq_dev_index = min(100, (freq_deviation_hz / self.FREQUENCY_TOLERANCE_HZ) * 100)
        freq_component = freq_dev_index * 0.30
        
        # Transformer temperature (0.20 weight)
        temp_component = metrics.transformer_temp_pct * 0.20
        
        # Renewable penetration (negative, -0.10 weight) — lowers GSI
        renewable_component = metrics.renewable_penetration_pct * 0.10
        
        gsi_score = load_component + freq_component + temp_component - renewable_component
        gsi_score = max(0, min(100, gsi_score))  # Clamp to 0-100
        
        return self._classify_gsi(gsi_score)
    
    def _classify_gsi(self, gsi_score: float) -> GridStressLevel:
        """Map GSI score to policy tier"""
        
        if gsi_score <= 30:
            return GridStressLevel(
                gsi_score=gsi_score,
                status="🟢 Green (Low Stress)",
                charging_policy="All slots open; fast charging allowed",
                max_power_kw=150.0,
                allow_new_connections=True,
                v2g_enabled=False
            )
        elif gsi_score <= 55:
            return GridStressLevel(
                gsi_score=gsi_score,
                status="🟡 Yellow (Moderate Stress)",
                charging_policy="Limit new connections; throttle to 80% power",
                max_power_kw=120.0,
                allow_new_connections=True,
                v2g_enabled=False
            )
        elif gsi_score <= 75:
            return GridStressLevel(
                gsi_score=gsi_score,
                status="🟠 Orange (High Stress)",
                charging_policy="Priority-only slots; defer non-urgent sessions",
                max_power_kw=50.0,
                allow_new_connections=False,
                v2g_enabled=False
            )
        else:
            return GridStressLevel(
                gsi_score=gsi_score,
                status="🔴 Red (Critical Stress)",
                charging_policy="Emergency vehicles only; V2G discharge activated",
                max_power_kw=22.0,
                allow_new_connections=False,
                v2g_enabled=True
            )
    
    def predict_gsi_spike(self, current_metrics: GridMetrics, 
                         time_window_minutes: int = 30) -> Optional[float]:
        """
        Placeholder for LSTM-based GSI prediction.
        In production, this would use historical + weather + event data.
        """
        # TODO: Integrate LSTM model trained on utility data
        # For now, return None (no prediction)
        return None
