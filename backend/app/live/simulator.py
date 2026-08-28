"""Deterministic offline train movement provider backed by repository CSV data."""

from datetime import datetime, timezone
from typing import Any

from app.repositories.traffic_repository import TrafficRepository
from app.live.provider import LiveTrainProvider, NormalizedLiveTrain


class SimulatedLiveTrainProvider(LiveTrainProvider):
    source = "SIMULATED"
    provider_name = "simulation"

    def __init__(self, traffic_repository: TrafficRepository | None = None):
        self.traffic_repository = traffic_repository or TrafficRepository()

    def get_train_positions(self) -> list[dict[str, Any]]:
        timetable = self.traffic_repository.get_timetable()
        delays = self.traffic_repository.get_live_delays()
        if timetable.empty:
            return []

        latest_delays = delays.sort_values("date").drop_duplicates("train_number", keep="last") if not delays.empty else delays
        if not latest_delays.empty:
            latest_delays = latest_delays.assign(train_number=latest_delays["train_number"].astype(str))
        delay_map = latest_delays.set_index("train_number").to_dict("index") if not latest_delays.empty else {}
        positions = []
        for row in timetable.drop_duplicates("train_number").to_dict("records"):
            train_id = str(row["train_number"])
            delay = delay_map.get(train_id, {}).get("delay_minutes", 0)
            delay = int(float(delay)) if delay == delay else 0
            status = "ON_TIME" if delay <= 5 else "MINOR_DELAY" if delay <= 30 else "MAJOR_DELAY"
            received_at = datetime.now(timezone.utc).isoformat()
            positions.append(NormalizedLiveTrain(
                train_id=train_id,
                train_number=train_id,
                train_type=str(row.get("train_type", "UNKNOWN")),
                current_segment=str(row.get("section_id", "")),
                latitude=None,
                longitude=None,
                speed=None,
                heading=None,
                current_station=None,
                next_station=None,
                delay_minutes=delay,
                status=status,
                event_time=str(delay_map.get(train_id, {}).get("actual_time") or row.get("scheduled_departure", "")),
                received_at=received_at,
                source=self.source,
                freshness_seconds=0,
            ).model_dump())
        return positions


SimulationLiveProvider = SimulatedLiveTrainProvider
