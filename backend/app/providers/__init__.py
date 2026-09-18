"""
Data Provider Registry for RailBlock AI.
"""

from app.providers.base import (
    MaintenanceDataProvider,
    COAProvider,
    GoodsForecastProvider,
    TrainDataProvider,
)
from app.providers.csv_providers import (
    CSVMaintenanceDataProvider,
    CSVCOAProvider,
    CSVGoodsForecastProvider,
    CSVTrainDataProvider,
)
from app.providers.future_adapters import (
    CRISTMSLiveAdapter,
    CRISCOALiveAdapter,
    CRISFOISLiveAdapter,
)

__all__ = [
    "MaintenanceDataProvider",
    "COAProvider",
    "GoodsForecastProvider",
    "TrainDataProvider",
    "CSVMaintenanceDataProvider",
    "CSVCOAProvider",
    "CSVGoodsForecastProvider",
    "CSVTrainDataProvider",
    "CRISTMSLiveAdapter",
    "CRISCOALiveAdapter",
    "CRISFOISLiveAdapter",
]
