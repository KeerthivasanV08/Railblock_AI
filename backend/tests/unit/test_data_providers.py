"""
Unit Tests for Data Provider Abstractions & Future Enterprise Adapters.
"""

import pytest
from app.providers import (
    CSVMaintenanceDataProvider,
    CSVCOAProvider,
    CSVGoodsForecastProvider,
    CSVTrainDataProvider,
    CRISTMSLiveAdapter,
    CRISCOALiveAdapter,
    CRISFOISLiveAdapter,
)


def test_csv_maintenance_data_provider():
    provider = CSVMaintenanceDataProvider()
    tms = provider.get_tms_defects()
    assert not tms.empty
    assert "task_id" in tms.columns

    smms = provider.get_smms_defects()
    assert not smms.empty
    assert "signal_id" in smms.columns or "task_id" in smms.columns

    tdms = provider.get_tdms_defects()
    assert not tdms.empty
    assert "mast_number" in tdms.columns or "task_id" in tdms.columns

    prov = provider.get_provider_provenance()
    assert prov["provider_type"] == "CSV_CALIBRATED_SYNTHETIC"
    assert "disclaimer" in prov


def test_csv_coa_provider():
    provider = CSVCOAProvider()
    sections = provider.get_corridor_sections()
    assert len(sections) == 68
    assert "section_id" in sections.columns

    cap = provider.get_section_capacity_utilization()
    assert not cap.empty

    prov = provider.get_provider_provenance()
    assert prov["provider_type"] == "DERIVED_CORRIDOR_SIMULATION"


def test_csv_goods_forecast_provider():
    provider = CSVGoodsForecastProvider()
    forecast = provider.get_freight_rake_forecast()
    assert not forecast.empty
    assert "freight_rakes_daily" in forecast.columns

    stats = provider.get_commodity_statistics()
    assert not stats.empty

    prov = provider.get_provider_provenance()
    assert prov["provider_type"] == "DERIVED_FREIGHT_MODEL"


def test_csv_train_data_provider():
    provider = CSVTrainDataProvider()
    tt = provider.get_passenger_timetable()
    assert not tt.empty

    occ = provider.get_train_section_occupancy()
    assert not occ.empty
    assert "section_distance_km" in occ.columns or "train_number" in occ.columns


def test_future_live_enterprise_adapters_raise_not_implemented():
    tms_live = CRISTMSLiveAdapter()
    with pytest.raises(NotImplementedError):
        tms_live.get_tms_defects()

    coa_live = CRISCOALiveAdapter()
    with pytest.raises(NotImplementedError):
        coa_live.get_corridor_sections()

    fois_live = CRISFOISLiveAdapter()
    with pytest.raises(NotImplementedError):
        fois_live.get_freight_rake_forecast()

    # Verify truthful provenance disclosures
    assert tms_live.get_provider_provenance()["status"] == "INTEGRATION_READY_STUB"
    assert coa_live.get_provider_provenance()["status"] == "INTEGRATION_READY_STUB"
    assert fois_live.get_provider_provenance()["status"] == "INTEGRATION_READY_STUB"
