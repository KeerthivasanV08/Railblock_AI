# RailBlock AI — Data Dictionary

## 1. Overview
This data dictionary documents all fields, types, allowed values, generation logic, and sources for the synthetic railway operations dataset powering **RailBlock AI**.

---

## 2. Raw Datasets

### A. Network & Infrastructure
#### `stations.csv`
- `station_code` (String, Primary Key): Unique 3-4 letter station code.
- `station_name` (String): Full station name.
- `chainage_km` (Float): Monotonically increasing linear distance along corridor (0.0 to 200.0 km).
- `division` (String): Administrative railway division ("Prayagraj (ALD)").
- `latitude` (Float): WGS84 latitude coordinate.
- `longitude` (Float): WGS84 longitude coordinate.

#### `block_sections.csv`
- `section_id` (String, Primary Key): Unique block section ID (`SEC_001` to `SEC_049`).
- `from_station` (String, FK): Origin station code.
- `to_station` (String, FK): Destination station code.
- `start_km` (Float): Section start chainage.
- `end_km` (Float): Section end chainage (`start_km` of section N+1 = `end_km` of section N).
- `line_type` (String): High Density Network category (`HDN`, `HUN`, `Branch`).
- `num_lines` (Integer): Track lines count (1, 2, 3, 4).
- `max_speed_kmph` (Integer): Maximum permissible speed (110, 130, 160).

---

### B. Maintenance & Defects
#### `tms_defects.csv` (Track Management System)
- `task_id` (String, Primary Key): Unique task identifier.
- `section_id` (String, FK): Block section ID.
- `start_km` (Float): Defect start chainage.
- `end_km` (Float): Defect end chainage.
- `defect_type` (String): Track defect category.
- `severity_class` (String): Severity ranking (`A`, `B`, `C`).
- `logged_date` (ISO Date): Logged date timestamp.
- `target_completion_date` (ISO Date): Target resolution date.
- `deferred_count` (Integer): Count of previous deferrals.
- `status` (String): Current status (`Open`, `Deferred`, `Completed`, `In-Progress`).

#### `smms_defects.csv` (Signal Management System)
- `task_id` (String, Primary Key): Unique task identifier.
- `section_id` (String, FK): Block section ID.
- `signal_id` (String, FK): Signal asset reference ID.
- `defect_type` (String): Signal defect category.
- `severity_class` (String): Severity ranking (`A`, `B`, `C`).

#### `tdms_defects.csv` (Traction Distribution Management System)
- `task_id` (String, Primary Key): Unique task identifier.
- `section_id` (String, FK): Block section ID.
- `mast_number` (String, FK): OHE mast reference identifier.
- `defect_type` (String): OHE defect category.
- `severity_class` (String): Severity ranking (`A`, `B`, `C`).

---

## 3. Processed Datasets
- `unified_maintenance_tasks.csv`: Unified schema combining TMS, SMMS, and TDMS.
- `spatially_mapped_tasks.csv`: Geo-spatial translated coordinates (GPS Lat/Lon & Mapped Chainage).
- `scored_tasks.csv`: Tasks enriched with MDPS model criticality scores (0-100), rank, and priority band.
- `clustered_tasks.csv`: Shadow-block and integrated mega-block clusters.
- `feasibility_checked_tasks.csv`: Operational feasibility flags and rejection reasons.
- `planning_features.csv`: Master features dataset for downstream planning AI algorithms.
