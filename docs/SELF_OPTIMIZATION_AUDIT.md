# RAILBLOCK AI — SELF-OPTIMIZATION ENGINE AUDIT REPORT
**Corridor**: Chennai Egmore → Thoothukudi (Tamil Nadu)  
**Author**: RailBlock AI Core Systems Architecture Team  
**Status**: AUDITED & HARDENED

---

## 1. Executive Summary
The Self-Optimization Engine in RailBlock AI operates at the tactical and strategic planning horizon (weekly schedules to 26-week rolling plans). It maximizes track maintenance throughput and asset safety while minimizing train timetable disruptions and machinery deadheading.

This audit resolved objective formulation ambiguities, introduced calibrated multi-objective weights, implemented a genuine 26-week rolling block planning engine, and established an adaptive closed-loop feedback mechanism.

---

## 2. Multi-Objective Mathematical Formulation
The OR-Tools MILP solver optimizes the binary selection variable $x_i \in \{0, 1\}$ for candidate maintenance block possession $i$:

$$\max \sum_{i=1}^n \left( \lambda_{\text{priority}} \cdot \text{MDPS}_i + \lambda_{\text{overlap}} \cdot \text{Overlap}_i + \lambda_{\text{seasonal}} \cdot \text{SRS\_Bonus}_i - \lambda_{\text{density}} \cdot \text{Traffic}_i - \lambda_{\text{delay}} \cdot \text{Delay}_i - \lambda_{\text{wastage}} \cdot \text{Wastage}_i \right) x_i$$

Subject to hard constraints:
1. **Daily Corridor Quota**: $\sum_{i=1}^n x_i \le M_{\text{daily}}$ (default: 15 blocks/day).
2. **Train Delay Ceiling**: $\sum_{i=1}^n \text{Delay}_i \cdot x_i \le \Delta_{\max}$ (default: 120 minutes).
3. **Fleet Limits**: $\sum_{i \in \text{Fleet}_k} x_i \le C_k$ (e.g. BCM $\le 3$, Tamping $\le 4$, Tower Wagon $\le 6$).
4. **Section Concurrency Limit**: $\sum_{i \in \text{Section}_s} x_i \le 3$ (prevents over-concentrating possessions on one track section).

### Calibrated Objective Weights (`OptimizationObjectiveWeights`)
- $\lambda_{\text{priority}} = 1.0$: Direct MDPS task criticality risk coverage (0-100).
- $\lambda_{\text{overlap}} = 20.0$: Multi-department shadow-block consolidation bonus.
- $\lambda_{\text{seasonal}} = 15.0$: Proactive pre-monsoon urgency bonus for vulnerable sections.
- $\lambda_{\text{density}} = 30.0$: Heavy traffic corridor congestion penalty.
- $\lambda_{\text{delay}} = 0.5$: Per-minute expected passenger train delay penalty.
- $\lambda_{\text{resource}} = 5.0$: Machine repositioning / deadheading friction penalty.
- $\lambda_{\text{wastage}} = 0.15$: Unused possession window buffer penalty.

---

## 3. Rolling 26-Week Planning Horizon
Unlike static planning that duplicates weekly schedules, the hardened `generate_rolling_plan(horizon_weeks=26)` implements:
1. **Task Overdue Accumulation**: Unserviced tasks accumulate 7 overdue days per future week:
   $$D_{\text{overdue}}(w) = D_{\text{overdue}}(0) + 7 \cdot (w - 1)$$
2. **MDPS Deferred Risk Multiplication**: Deferred tasks compound urgency:
   $$\text{MDPS}(w) = \min\left(99, (\text{Base} + 0.4 \cdot D_{\text{overdue}}) \cdot (1 + 0.25 \cdot N_{\text{deferred}})\right)$$
3. **Corridor Seasonal Modulation**: Applies historical weather risk curves for Tamil Nadu (Northeast Monsoon in Oct–Dec elevates SRS to 65+, triggering prioritized pre-monsoon drainage and ballast work).
4. **Scheduled Recurring Cyclic Maintenance**: Injects mandatory inspection intervals:
   - Ultrasonic Rail Flaw Detection (every 4 weeks)
   - TRD OHE Catenary Patrol (every 6 weeks)
   - S&T Point Machine & Interlocking Tests (every 8 weeks)
   - Mechanized Heavy Tamping (every 12 weeks).

---

## 4. Closed-Loop Execution Feedback & Re-Optimization
The closed loop connects field reality back to future optimization:
```text
PLAN (MILP) → APPROVE → EXECUTE → RECORD (execution_outcomes.csv)
                                              ↓
RE-OPTIMIZE ← CALIBRATE BUFFERS ← LEARN (feedback_engine.py)
```
- **Duration Variance Tracking**: Compares planned duration vs actual duration.
- **Overrun Rate**: Detects sections with recurrent execution overruns (>15 min).
- **Adaptive Buffer Calibration**: Learns an extra duration buffer (+10 to +30 min) for friction-heavy sections, preventing cascading delays in subsequent weekly plan generations.
