# Goods Train Forecast & Freight Traffic Provenance (GOODS_FORECAST_PROVENANCE.md)

This document provides transparent, truthful provenance documentation for goods train forecasting and freight traffic modeling within **RailBlock AI** (SIH Problem Statement 26027).

---

## 1. Provenance Classification: `DERIVED / SIMULATED`

- **Authoritative Baseline Source**: 
  1. Ministry of Railways Annual Statistical Statements (2010-11 to 2023-24) — Revenue commodity freight loading by commodity type (Coal, Raw Materials for Steel, Pig Iron & Finished Steel, Iron Ore, Cement, Food Grains, Fertilisers, Mineral Oil, Container Traffic).
  2. Southern Railway Performance Review 2023-24 — Operational indicators including average wagon turnaround days (3.92 days), net-tonne-km (38.60 billion), and operating ratio (128.40).
- **Corridor Application**: Chennai Egmore $\rightarrow$ Thoothukudi Corridor (648 km, 68 block sections).
- **CRIS / FOIS Live Connectivity**: **NOT CONNECTED TO LIVE CRIS FOIS IN PROTOTYPE**.
  *Indian Railways Freight Operations Information System (FOIS) is an internal railway intranet system requiring CRIS enterprise token authorization and divisional VPN infrastructure. RailBlock AI models freight movements using calibrated zonal distributions rather than fabricating a real connection.*

---

## 2. Derivation Methodology

1. **Port Feeder Freight Demand**:
   The southern terminus of the corridor connects to **V.O. Chidambaranar Port (Thoothukudi)**, which feeds heavy bulk freight (thermal coal for Tuticorin Thermal Power Station / TTPS, copper concentrate, rock phosphate fertilisers, marine salt, and container traffic) northward through Madurai, Tiruchirappalli, and Chengalpattu toward Chennai.

2. **Daily Rake Generation**:
   In `process_freight_and_traffic.py` (lines 108–110), freight rake density per block section is sampled from calibrated empirical loading rates:
   $$\text{freight\_rakes\_daily} \in [8, 10, 12, 14, 16, 18] \text{ rakes/day}$$
   
3. **Total Section Trains & Headway**:
   $$\text{daily\_total\_trains} = \text{passenger\_trains\_daily} + \text{freight\_rakes\_daily}$$
   $$\text{average\_headway\_minutes} = \frac{1440.0}{\text{daily\_total\_trains}}$$

4. **Section Capacity Utilization Benchmark**:
   $$\text{practical\_capacity} = \begin{cases} 60 \text{ trains/day} & \text{for double-line sections (HDN)} \\ 28 \text{ trains/day} & \text{for single-line sections} \end{cases}$$
   $$\text{capacity\_utilization\_percent} = \frac{\text{daily\_total\_trains}}{\text{practical\_capacity}} \times 100$$
   *This reflects CAG Report 45 Table 21 findings showing high-density routes operating above 100% capacity utilization.*

---

## 3. Usage in Block Optimization

1. **Tripartite Hard Feasibility Gate** (`ConstraintEngine.check_feasibility()` in `constraints.py`):
   $$\text{traffic\_density} = \frac{\text{capacity\_utilization\_percent}}{100.0}$$
   $$\text{traffic\_feasible} = (\text{traffic\_density} < 0.85)$$
   *If passenger + goods traffic density exceeds 85%, candidate block windows are rejected with reason: `High Traffic Pressure / No Traffic Gap`.*

2. **MILP Objective Density Penalty** (`OptimizationObjective` in `objective.py`):
   Candidate blocks are penalized in the objective function by:
   $$- (\text{traffic\_density} \times w_{\text{density}})$$
   where $w_{\text{density}} = 30.0$, steering maintenance blocks into natural nocturnal and low-density operational windows between scheduled passenger and freight paths.

---

## 4. Integration-Ready Provider Interface

The abstract contract `GoodsForecastProvider` in `app.providers.base` defines:
- `get_freight_rake_forecast()`
- `get_commodity_statistics()`

When deployed on the Indian Railways intranet, `CRISFOISLiveAdapter` (`app.providers.future_adapters`) can be configured with enterprise credentials to consume real-time rake assignments directly from FOIS without altering downstream optimization logic.
