# RailBlock AI — Data Sources & Synthesis Policy

## 1. Synthetic Data Policy
All operational, defect, traffic, delay, slot, and historical dataset records generated within `data/raw/` are synthetic. They are programmatically synthesized using Indian Railways operational rules, domain configurations, linear geometry interpolation, and controlled stochastic statistical distributions.

---

## 2. Domain Alignment Reference Sources
1. **TMS (Track Management System)**: Modeled after Indian Railways Civil Engineering Track Maintenance Manual (IRTMM) defect categorization and inspection intervals.
2. **SMMS (Signal & Interlocking System)**: Modeled after Signal Engineering Manual (IRSEM) failure logs and signal reference layout rules.
3. **TDMS (Traction Distribution System)**: Modeled after Overhead Equipment (OHE) maintenance rules (TI/MI manuals) and mast spacing standards.
4. **COA (Control Office Application)**: Modeled after operational train movement control charts, timetable schedules, and section capacity slot allocation rules on HDN routes.
