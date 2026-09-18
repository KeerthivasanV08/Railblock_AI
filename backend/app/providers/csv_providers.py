"""
Concrete CSV / Calibrated Simulation Data Providers for RailBlock AI.

These providers read from the local repository datasets, ensuring strictly accurate
provenance labeling (CALIBRATED_SYNTHETIC, DERIVED, REAL_OGD).
"""

from typing import Dict
import pandas as pd
from app.config.settings import settings
from app.repositories.csv_repository import CSVRepository
from app.providers.base import (
    MaintenanceDataProvider,
    COAProvider,
    GoodsForecastProvider,
    TrainDataProvider,
)


class CSVMaintenanceDataProvider(MaintenanceDataProvider):
    """
    Supplies fixed infrastructure maintenance data from calibrated synthetic datasets
    grounded in CAG Report 45 benchmarks and corridor topology.
    """

    def __init__(self):
        self.tms_path = settings.DATA_ROOT / "calibrated/maintenance/tms_defects.csv"
        self.smms_path = settings.DATA_ROOT / "calibrated/maintenance/smms_defects.csv"
        self.tdms_path = settings.DATA_ROOT / "calibrated/maintenance/tdms_defects.csv"
        self.unified_path = settings.PROCESSED_DATA_ROOT / "unified_maintenance_tasks.csv"

    def get_tms_defects(self) -> pd.DataFrame:
        if self.tms_path.exists():
            return CSVRepository(self.tms_path).read_csv()
        return CSVRepository(settings.RAW_DATA_ROOT / "defects/tms_defects.csv").read_csv()

    def get_smms_defects(self) -> pd.DataFrame:
        if self.smms_path.exists():
            return CSVRepository(self.smms_path).read_csv()
        return CSVRepository(settings.RAW_DATA_ROOT / "defects/smms_defects.csv").read_csv()

    def get_tdms_defects(self) -> pd.DataFrame:
        if self.tdms_path.exists():
            return CSVRepository(self.tdms_path).read_csv()
        return CSVRepository(settings.RAW_DATA_ROOT / "defects/tdms_defects.csv").read_csv()

    def get_unified_maintenance_tasks(self) -> pd.DataFrame:
        return CSVRepository(self.unified_path).read_csv()

    def get_provider_provenance(self) -> Dict[str, str]:
        return {
            "provider_type": "CSV_CALIBRATED_SYNTHETIC",
            "tms_source": "Calibrated TMS Track Maintenance Model (CAG Report 45 benchmarks)",
            "smms_source": "Calibrated SMMS S&T Maintenance Model (standardized RB-SIG taxonomy)",
            "tdms_source": "Calibrated TDMS TRD Maintenance Model (standardized RB-OHE taxonomy)",
            "unified_source": "data/processed/unified/unified_maintenance_tasks.csv (80,000 tasks)",
            "disclaimer": "Ground-truth CRIS database connectivity is not available in prototype environment."
        }


class CSVCOAProvider(COAProvider):
    """
    Supplies corridor section capacity and block window definitions from derived OSM/topology models.
    """

    def __init__(self):
        self.sections_path = settings.DATA_ROOT / "processed/network/block_sections.csv"
        self.traffic_path = settings.DATA_ROOT / "derived/traffic/enriched_traffic.csv"

    def get_corridor_sections(self) -> pd.DataFrame:
        return CSVRepository(self.sections_path).read_csv()

    def get_section_capacity_utilization(self) -> pd.DataFrame:
        return CSVRepository(self.traffic_path).read_csv()

    def get_provider_provenance(self) -> Dict[str, str]:
        return {
            "provider_type": "DERIVED_CORRIDOR_SIMULATION",
            "sections_source": "OSM Railway Infrastructure Topology Master (68 block sections)",
            "capacity_source": "RailBlock Corridor Traffic Integration Engine (headway & capacity ratio)",
            "disclaimer": "Live CRIS COA operational chart socket is not available in prototype environment."
        }


class CSVGoodsForecastProvider(GoodsForecastProvider):
    """
    Supplies goods train rake forecasts and commodity freight records from derived traffic models.
    """

    def __init__(self):
        self.traffic_path = settings.DATA_ROOT / "derived/traffic/enriched_traffic.csv"
        raw_path = settings.DATA_ROOT / "raw/traffic/freight_statistics.csv"
        real_path = settings.DATA_ROOT / "real/traffic/freight_statistics.csv"
        self.freight_path = raw_path if raw_path.exists() else real_path

    def get_freight_rake_forecast(self) -> pd.DataFrame:
        df = CSVRepository(self.traffic_path).read_csv()
        cols = ["section_id", "freight_rakes_daily", "total_trains_daily", "capacity_utilization_percent"]
        filtered_cols = [c for c in cols if c in df.columns]
        return pd.DataFrame(df[filtered_cols])

    def get_commodity_statistics(self) -> pd.DataFrame:
        return CSVRepository(self.freight_path).read_csv()

    def get_provider_provenance(self) -> Dict[str, str]:
        return {
            "provider_type": "DERIVED_FREIGHT_MODEL",
            "forecast_source": "Southern Railway freight loading & Thoothukudi port feeder rake distribution",
            "commodity_source": "Ministry of Railways Annual Statistical Statements (2010-11 to 2023-24)",
            "disclaimer": "Live CRIS FOIS rake tracking API is not available in prototype environment."
        }


class CSVTrainDataProvider(TrainDataProvider):
    """
    Supplies passenger train timetable and section traversal windows from authentic OGD data.
    """

    def __init__(self):
        self.raw_timetable_path = settings.DATA_ROOT / "raw/timetable/ogd/railway_train_details_original.csv"
        self.occupancy_path = settings.DATA_ROOT / "processed/timetable/train_section_occupancy.csv"

    def get_passenger_timetable(self) -> pd.DataFrame:
        return CSVRepository(self.raw_timetable_path).read_csv()

    def get_train_section_occupancy(self) -> pd.DataFrame:
        return CSVRepository(self.occupancy_path).read_csv()

    def get_provider_provenance(self) -> Dict[str, str]:
        return {
            "provider_type": "AUTHENTIC_OGD_HISTORICAL",
            "timetable_source": "Ministry of Railways / CRIS via data.gov.in (186k national stop records)",
            "occupancy_source": "Derived section traversal windows for Chennai-Thoothukudi corridor (1,259 windows)",
            "disclaimer": "Baseline dataset is historical (2017 baseline with 2024 calibrated corridor alignments)."
        }
