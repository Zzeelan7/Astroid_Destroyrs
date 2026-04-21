"""Unit tests for GSI Engine"""
import pytest
from datetime import datetime
from app.core.gsi_engine import GSIEngine, GridMetrics


@pytest.fixture
def gsi_engine():
    return GSIEngine()


def test_gsi_green_status(gsi_engine):
    """Test Green status (GSI <= 30)"""
    metrics = GridMetrics(
        timestamp=datetime.now(),
        load_percentage=20,
        frequency_hz=50.0,
        transformer_temp_pct=30,
        renewable_penetration_pct=50
    )
    result = gsi_engine.compute_gsi(metrics)
    assert result.gsi_score <= 30
    assert "🟢" in result.status
    assert result.max_power_kw == 150.0


def test_gsi_yellow_status(gsi_engine):
    """Test Yellow status (30 < GSI <= 55)"""
    metrics = GridMetrics(
        timestamp=datetime.now(),
        load_percentage=50,
        frequency_hz=50.0,
        transformer_temp_pct=50,
        renewable_penetration_pct=30
    )
    result = gsi_engine.compute_gsi(metrics)
    assert 30 < result.gsi_score <= 55
    assert "🟡" in result.status


def test_gsi_critical_status(gsi_engine):
    """Test Red status with V2G (GSI > 75)"""
    metrics = GridMetrics(
        timestamp=datetime.now(),
        load_percentage=95,
        frequency_hz=49.5,
        transformer_temp_pct=85,
        renewable_penetration_pct=5
    )
    result = gsi_engine.compute_gsi(metrics)
    assert result.gsi_score > 75
    assert "🔴" in result.status
    assert result.v2g_enabled is True


def test_renewable_lowers_gsi(gsi_engine):
    """Test that high renewable % reduces GSI"""
    metrics_low_renewable = GridMetrics(
        timestamp=datetime.now(),
        load_percentage=60,
        frequency_hz=50.0,
        transformer_temp_pct=60,
        renewable_penetration_pct=10
    )
    
    metrics_high_renewable = GridMetrics(
        timestamp=datetime.now(),
        load_percentage=60,
        frequency_hz=50.0,
        transformer_temp_pct=60,
        renewable_penetration_pct=90
    )
    
    low_ren_gsi = gsi_engine.compute_gsi(metrics_low_renewable).gsi_score
    high_ren_gsi = gsi_engine.compute_gsi(metrics_high_renewable).gsi_score
    
    assert high_ren_gsi < low_ren_gsi
