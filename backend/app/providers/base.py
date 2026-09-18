"""
Abstract Data Provider Interfaces for RailBlock AI (SIH PS 26027).

Defines clear provider contracts separating prototype data sources (calibrated synthetic,
derived statistics, and public OGD datasets) from future live Indian Railways enterprise feeds
(CRIS TMS/SMMS/TDMS, COA, and FOIS).
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import pandas as pd


class MaintenanceDataProvider(ABC):
    """
    Abstract interface for multi-departmental fixed infrastructure maintenance data
    (Track, Signal & Telecom, Traction Distribution).
    """

    @abstractmethod
    def get_tms_defects(self) -> pd.DataFrame:
        """Returns Engineering track defects and overdue maintenance records."""
        raise NotImplementedError

    @abstractmethod
    def get_smms_defects(self) -> pd.DataFrame:
        """Returns Signal & Telecommunication defects and interlocking maintenance tasks."""
        raise NotImplementedError

    @abstractmethod
    def get_tdms_defects(self) -> pd.DataFrame:
        """Returns Traction Distribution (OHE/Substation) defects and maintenance tasks."""
        raise NotImplementedError

    @abstractmethod
    def get_unified_maintenance_tasks(self) -> pd.DataFrame:
        """Returns normalized multi-department task register across all disciplines."""
        raise NotImplementedError

    @abstractmethod
    def get_provider_provenance(self) -> Dict[str, str]:
        """Returns truthful source provenance metadata for auditing."""
        raise NotImplementedError


class COAProvider(ABC):
    """
    Abstract interface for Control Office Application (COA) corridor block availability,
    capacity slots, and operational movement restrictions.
    """

    @abstractmethod
    def get_corridor_sections(self) -> pd.DataFrame:
        """Returns corridor topology and planning section definitions."""
        raise NotImplementedError

    @abstractmethod
    def get_section_capacity_utilization(self) -> pd.DataFrame:
        """Returns capacity utilization and headway metrics per block section."""
        raise NotImplementedError

    @abstractmethod
    def get_provider_provenance(self) -> Dict[str, str]:
        """Returns truthful source provenance metadata for auditing."""
        raise NotImplementedError


class GoodsForecastProvider(ABC):
    """
    Abstract interface for Freight Operations Information System (FOIS) goods train rakes,
    commodity freight output, and freight density forecasts.
    """

    @abstractmethod
    def get_freight_rake_forecast(self) -> pd.DataFrame:
        """Returns projected daily goods/freight rakes and section headways."""
        raise NotImplementedError

    @abstractmethod
    def get_commodity_statistics(self) -> pd.DataFrame:
        """Returns commodity-wise revenue loading and tonnage statistics."""
        raise NotImplementedError

    @abstractmethod
    def get_provider_provenance(self) -> Dict[str, str]:
        """Returns truthful source provenance metadata for auditing."""
        raise NotImplementedError


class TrainDataProvider(ABC):
    """
    Abstract interface for National Train Enquiry System (NTES) / Timetable train movements
    and passenger section occupancies.
    """

    @abstractmethod
    def get_passenger_timetable(self) -> pd.DataFrame:
        """Returns passenger train stop records and route traversal schedules."""
        raise NotImplementedError

    @abstractmethod
    def get_train_section_occupancy(self) -> pd.DataFrame:
        """Returns scheduled section occupancy traversal windows across the corridor."""
        raise NotImplementedError

    @abstractmethod
    def get_provider_provenance(self) -> Dict[str, str]:
        """Returns truthful source provenance metadata for auditing."""
        raise NotImplementedError
