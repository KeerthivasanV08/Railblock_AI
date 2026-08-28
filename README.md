# RailBlock AI

## AI-Powered Automatic Block Planning & Railway Operations Decision Support System

> **RailBlock AI** is an AI-assisted Railway Operations Command & Decision Centre designed to intelligently plan, consolidate, validate, monitor, and dynamically reschedule railway maintenance blocks while maximizing asset availability and minimizing disruption to train operations.

---

# 1. Product Overview

Indian Railways performs continuous maintenance of critical railway infrastructure such as:

- Tracks
- Bridges and civil assets
- Overhead Equipment (OHE)
- Signals
- Point machines
- Track circuits
- Axle counters
- Telecom infrastructure

These maintenance activities require temporary **blocks/disconnections** during which train movement through a particular railway section is restricted or stopped.

Today, maintenance requirements are generated independently by different departments and are often planned in a decentralized manner.

RailBlock AI introduces a centralized intelligence layer that brings these maintenance requirements together and determines:

> **What needs to be maintained, where it is located, how urgent it is, when it should be done, which resources are available, what other maintenance tasks can be combined, and what impact the proposed block will have on train operations.**

The system is designed as a **decision-support platform**, not an autonomous railway control system.

Human railway controllers remain responsible for approving, modifying, rejecting, and executing maintenance plans.

---

# 2. Problem Statement

## SIH Problem Statement

**Problem Statement ID: 26027**

### AI-Powered Automatic Block Planning to Maximize Asset Availability for Train Operations on Indian Railways

---

## 2.1 Existing Problem

Maintenance planning involves multiple departments operating with different systems and location references.

| Department | Responsibility | Existing System |
|---|---|---|
| Engineering | Track and civil infrastructure | TMS |
| Electrical / TRD | OHE and traction infrastructure | TDMS |
| S&T | Signals, telecom, interlocking | SMMS |
| Operations | Train movement and traffic control | COA |
| Block Management | Block/disconnection requests | BDMS |

The original problem identifies the decentralized and siloed nature of these processes as a major source of inefficient block utilization and operational disruption.

---

# 3. Core Operational Challenges

## 3.1 Departmental Silos

Engineering, TRD, and S&T may independently request blocks for nearby or overlapping locations.

Without a common intelligence layer:

```text
Engineering Request
       ↓
Separate Block

TRD Request
       ↓
Separate Block

S&T Request
       ↓
Separate Block
```

This can result in multiple blocks being allocated to the same corridor when the work could potentially have been performed together.

---

# 3.2 Shadow Block Wastage

Consider:

```text
TRD
09:00 ───────── 12:00
        BLOCK

Engineering
Next Day
10:00 ───────── 13:00
        BLOCK
```

If both activities are spatially compatible, they could potentially be consolidated:

```text
INTEGRATED BLOCK

09:00 ───────────────── 12:00

Engineering + TRD
```

This is the concept of **Shadow Block Consolidation**.

---

# 3.3 Demanded vs Granted Discrepancy

A maintenance department may request:

```text
Requested:
3 Hours
```

but due to traffic conditions may receive:

```text
Granted:
30 Minutes
```

This can lead to:

- incomplete maintenance
- repeated block requests
- additional asset downtime
- resource wastage
- increased operational pressure

RailBlock AI explicitly models this planning problem through historical block records.

---

# 3.4 Rolling Block Planning Complexity

Long-horizon planning requires considering:

- Thousands of maintenance tasks
- Train schedules
- Freight traffic
- Machine availability
- Crew availability
- Seasonal conditions
- Maintenance deadlines
- Existing blocks
- Resource movements
- Emergency events

RailBlock AI supports:

```text
Weekly Planning
      ↓
Monthly Planning
      ↓
26-Week Rolling Block Plan
```

---

# 3.5 Spatial Reference Fragmentation

Different railway systems may describe the same physical location differently.

For example:

```text
TMS
Km 118.45

TRD
Mast 120/15

S&T
Signal S-214

COA
Block Section SEC-021
```

RailBlock AI creates a common spatial representation so these references can be correlated.

---

# 4. RailBlock AI Solution

RailBlock AI acts as an intelligence and decision-support layer above existing railway systems.

```text
TMS ───────┐
SMMS ──────┤
TDMS ──────┤
COA ───────┤
BDMS ──────┤
           ↓
   RailBlock AI
           ↓
 ┌───────────────────────┐
 │ Spatial Intelligence  │
 │ Priority Intelligence │
 │ Block Consolidation   │
 │ Optimization          │
 │ Resource Feasibility  │
 │ XAI                   │
 │ Self-Healing Planning │
 └───────────────────────┘
           ↓
Human Controller
           ↓
Approved Maintenance Plan
```

The architecture intentionally avoids replacing existing railway operational systems.

Instead, RailBlock AI provides an intelligence layer capable of consuming their data and producing coordinated planning recommendations.

---

# 5. Product Objectives

RailBlock AI is designed to achieve the following objectives:

1. Increase railway asset availability.
2. Improve maintenance block utilization.
3. Consolidate compatible departmental maintenance activities.
4. Reduce unnecessary block requests.
5. Prioritize high-risk maintenance tasks.
6. Detect scheduling conflicts before approval.
7. Match maintenance activities with available resources.
8. Reduce train-operation disruption.
9. Support weekly and 26-week rolling planning.
10. Automatically generate alternative schedules during disruptions.
11. Provide explainable AI recommendations.
12. Preserve human authority over operational decisions.
13. Maintain complete auditability of planning decisions.

---

# 6. Core Product Philosophy

RailBlock AI follows five fundamental principles.

## 6.1 Spatial Truth First

All maintenance activities must be mapped to a common physical railway location before intelligent planning is performed.

---

## 6.2 AI Where AI Adds Value

Machine learning is used for:

- Priority prediction
- Risk estimation
- Pattern detection
- Recommendation support

Safety-critical scheduling decisions are not blindly delegated to ML.

---

## 6.3 Deterministic Safety Constraints

Hard operational constraints are enforced deterministically.

No AI recommendation should become an approved block unless the required constraints are satisfied.

The backend architecture explicitly separates ML, deterministic validation, and optimization for this reason.

---

## 6.4 Human-in-the-Loop

The system recommends.

The controller decides.

```text
AI Recommendation
       ↓
Human Review
       ↓
Approve / Modify / Reject
       ↓
Audit Log
```

---

## 6.5 Explainability

Every important AI recommendation should answer:

> **Why was this recommended?**

Instead of:

```text
Priority = 91
```

RailBlock AI explains:

```text
High severity
+ overdue maintenance
+ high traffic corridor
+ repeated deferrals
+ critical asset
----------------------
Priority Score = 91
```

---

# 7. High-Level System Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                       │
│                                                             │
│ Command Dashboard | Block Planner | Live Monitor            │
│ Maintenance Matrix | Resources | XAI | Analytics | Reports │
└──────────────────────────┬──────────────────────────────────┘
                           │
                     REST / WebSocket
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                         API LAYER                            │
│                                                             │
│ FastAPI | Request Validation | Routing | WebSocket          │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    INTELLIGENCE CORE                        │
│                                                             │
│ Spatial Translator                                         │
│ MDPS Priority Engine                                       │
│ Shadow Block Clustering                                    │
│ Constraint Engine                                          │
│ OR-Tools Optimization                                      │
│ Resource Feasibility                                        │
│ XAI Engine                                                  │
│ Self-Healing Rescheduler                                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    DATA / INTEGRATION                       │
│                                                             │
│ TMS | SMMS | TDMS | COA | BDMS | Resource Feeds            │
│                                                             │
│ PostgreSQL / PostGIS | Redis | CSV / Synthetic Data         │
└─────────────────────────────────────────────────────────────┘
```

---

# 8. End-to-End Product Flow

```text
DATA SOURCES
    ↓
Data Ingestion
    ↓
Validation & Normalization
    ↓
Spatial Translation
    ↓
Unified Maintenance Tasks
    ↓
MDPS Priority Scoring
    ↓
Shadow Block Detection
    ↓
Resource Feasibility
    ↓
Traffic / Corridor Constraint Checking
    ↓
OR-Tools Optimization
    ↓
Candidate Block Plan
    ↓
XAI Explanation
    ↓
Human Review
    ↓
Approve / Modify / Reject
    ↓
Scheduled Block
    ↓
Live Monitoring
    ↓
Disruption Detection
    ↓
Self-Healing Rescheduling
    ↓
Human Approval
    ↓
Updated Plan
    ↓
Audit + Analytics
```

---

# 9. Major Intelligence Modules

## 9.1 Universal Geo-Spatial Translator

### Purpose

Translate different railway location references into a unified geographic coordinate system.

### Inputs

- Track kilometres
- Mast numbers
- Signal IDs
- Block sections
- Station references

### Processing

```text
Department Reference
        ↓
Reference Lookup
        ↓
Section Identification
        ↓
Linear Referencing
        ↓
Unified Chainage
        ↓
Latitude / Longitude
```

### Example

```text
Mast 120/15
      ↓
Section SEC-021
      ↓
Chainage 118.45 km
      ↓
GPS Coordinate
```

This enables spatial correlation across departments.

---

# 10. MDPS — Multi-Department Priority Scoring

MDPS stands for:

> **Multi-Department Priority Score**

The purpose is to determine which maintenance activities should receive priority.

### Important factors

- Severity
- Overdue days
- Traffic density
- Asset criticality
- Previous deferrals
- Maintenance urgency
- Seasonal conditions

Output:

```text
0 ───────────────────── 100

Low       Medium       High       Critical
```

Example:

```text
Task: TMS-DEF-12452

Severity: Critical
Overdue: 14 days
Traffic: High
Deferrals: 3

MDPS Score: 94
Priority: Critical
```

The backend currently uses a Gradient Boosting based MDPS implementation for tabular priority inference.

---

# 11. Shadow Block Consolidation

The system identifies maintenance activities that can potentially share the same block.

Tasks are grouped based on:

### Spatial compatibility

```text
Task A → Km 118.2
Task B → Km 119.0
Task C → Km 118.7
```

### Temporal compatibility

```text
Task A → 09:00–11:00
Task B → 09:30–11:30
Task C → 09:00–12:00
```

### Operational compatibility

- Same or compatible corridor
- Compatible departments
- Compatible resource requirements
- Compatible safety conditions

Output:

```text
Individual Tasks
       ↓
Spatial + Temporal Clustering
       ↓
Shadow Block Cluster
       ↓
Integrated Mega Block
```

---

# 12. Resource Feasibility

A block is not considered operationally feasible simply because a time slot exists.

RailBlock AI evaluates:

```text
Maintenance Task
      +
Required Machine
      +
Required Crew
      +
Location
      +
Travel / Position
      +
Shift Availability
      +
Traffic Window
```

Example:

```text
Required:

Tamping Machine
P-Way Gang
3 Hours
Section SEC-018

Available:

Tamping Machine TM-04 ✓
P-Way Gang ENG-07 ✓
Traffic Window ✓
Crew Shift ✓

Result:
FEASIBLE
```

---

# 13. Constraint Engine

Railway scheduling contains hard constraints that cannot be ignored.

The system validates factors such as:

- Block window validity
- Train conflict
- Section occupancy
- Resource availability
- Crew availability
- Maintenance duration
- Existing block conflicts
- Operational safety boundaries

The backend design explicitly treats constraint validation as deterministic and safety-critical rather than relying solely on ML.

---

# 14. OR-Tools Optimization

Once candidate tasks and feasible windows are identified, the optimizer determines the best overall schedule.

### Optimization objectives

The system attempts to:

```text
MAXIMIZE

Asset Availability
+
Maintenance Completion
+
Block Utilization
+
Integrated Blocks

MINIMIZE

Train Delay
+
Unused Block Time
+
Task Deferrals
+
Resource Conflicts
+
Operational Disruption
```

Google OR-Tools MILP is used for schedule optimization because hard operational constraints can be encoded explicitly.

---

# 15. AI Recommendation Engine

The system produces recommendations such as:

```text
AI RECOMMENDATION

Block: RB-528

08:30 – 11:30

Departments:
Engineering
TRD
S&T

Tasks:
7

Priority:
94

Utilization:
91%

Train Impact:
Low
```

### Recommendation reasons

```text
✓ 7 spatially compatible tasks
✓ High-priority maintenance
✓ Suitable traffic window
✓ Required machines available
✓ Required crews available
✓ Low expected train impact
```

---

# 16. Explainable AI

Every important decision should be explainable.

Example:

```text
Why is Task TMS-12452 Priority 91?
```

The interface displays:

```text
Severity              ██████████  40
Overdue Risk          ████████    28
Traffic Impact        █████        15
Asset Criticality     ███           8
Deferral Risk         ━━━━━         5
-------------------------------------
Final Score                       91
```

### Natural-language explanation

> High priority because the defect has high severity, is overdue, is located on a heavily utilized corridor, and has previously been deferred multiple times.

---

# 17. Human Approval Workflow

RailBlock AI does not automatically execute maintenance decisions.

## Lifecycle

```text
Draft
  ↓
AI Recommended
  ↓
Pending Approval
  ↓
Approved
  ↓
Scheduled
  ↓
Active
  ↓
Completed
```

Alternative:

```text
AI Recommended
      ↓
    Rejected
```

Or:

```text
AI Recommended
      ↓
    Modified
      ↓
  Re-validated
      ↓
    Approved
```

The backend approval design supports explicit approve, modify, reject, and execute transitions.

---

# 18. Live Corridor Monitoring

The Live Operations interface provides simulated operational awareness.

It displays:

- Train positions
- Train delays
- Active blocks
- Maintenance activities
- Machine positions
- Crew availability
- Defects
- Disruption events

The current backend supports a simulated WebSocket live stream for train positions, block state transitions, and disruption alerts.

---

# 19. Self-Healing Rescheduler

Railway operations can change after a block has already been planned.

Possible disruptions include:

1. Train delay
2. Block overrun
3. Emergency defect
4. Machine breakdown

The backend currently recognizes these disruption categories.

### Example

```text
ORIGINAL BLOCK

RB-402
09:00 – 12:00
```

A train delay occurs:

```text
Train G-88
Delay: 42 minutes
```

The system identifies the impact:

```text
Affected Block: RB-402
```

Then generates alternatives:

```text
OPTION A
10:45 – 13:45
Impact: Low

OPTION B
14:00 – 17:00
Impact: Medium

OPTION C
Next Day
Impact: High
```

The controller selects the preferred alternative.

---

# 20. Frontend

The frontend is designed as a **Railway Operations Command & Decision Centre**, rather than a generic SaaS dashboard.

The current frontend specification includes a desktop-first command-centre interface with operational dashboards, timeline planning, task analysis, resources, disruption handling, analytics, reports, and administration.

---

# 21. Frontend Technology

```text
React
TypeScript
Vite
Tailwind CSS
shadcn/ui
Radix UI
Zustand
TanStack Query
React Hook Form
Zod
Recharts
MapLibre GL / spatial visualization
WebSocket
Vitest
React Testing Library
Playwright / Cypress
```

---

# 22. Frontend Pages

## Command Dashboard

Route:

```text
/dashboard
```

Displays:

- Asset availability
- Active blocks
- Critical defects
- Overdue tasks
- Block utilization
- Integrated blocks
- Potential time saved
- Pending approvals
- Corridor visualization
- AI insights
- Disruption alerts

---

## AI Block Planner

Route:

```text
/planner
```

Primary planning workstation.

Features:

- Multi-lane timeline
- Train movements
- Department blocks
- Integrated blocks
- Drag and resize
- Conflict detection
- AI plan generation
- Plan comparison
- Block approval
- Block modification
- Block rejection
- Block locking
- Simulation

The current frontend design uses a seven-lane planning timeline covering passenger, express, freight, Engineering, TRD, S&T and integrated blocks.

---

## Live Corridor Monitor

Route:

```text
/live
```

Displays:

- Train movement
- Active blocks
- Machine location
- Crew status
- Defect markers
- Disruption alerts
- Upcoming blocks
- Train delays

---

## Maintenance Task Matrix

Route:

```text
/tasks
```

Provides a searchable, filterable maintenance task workspace.

Columns include:

```text
Task ID
Department
Asset
Location
Defect
Severity
Overdue Days
Priority Score
Previous Deferrals
Required Duration
Required Resource
Status
Recommended Block
```

The frontend is designed to handle the synthetic 25,000+ task dataset using pagination rather than rendering every row simultaneously.

---

## Task Explainability

Route:

```text
/tasks/:taskId
```

Displays:

- Priority score
- Factor breakdown
- AI explanation
- Defect history
- Related planning information
- Recommended block
- Navigation to planner

---

## AI Recommendations

Routes:

```text
/recommendations
/recommendations/:id
```

Displays:

- AI recommendations
- Recommendation reasons
- Priority factors
- Estimated impact
- Resource availability
- Approve
- Modify
- Reject
- Simulate

---

## Resource Availability

Route:

```text
/resources
```

Displays:

### Machines

- Tamping machines
- Ballast cleaning machines
- Tower wagons
- Rail grinders
- Inspection vehicles

### Crew

- P-Way gangs
- TRD crews
- S&T crews

Also includes:

- Resource calendar
- Availability status
- Machine locations
- Assignment information

---

## Self-Healing Console

Routes:

```text
/disruptions
/disruptions/:eventId
```

Displays:

- Disruption events
- Affected blocks
- Train impact
- Rescheduling alternatives
- Before/after simulation
- Apply reschedule
- Audit information

---

## Analytics

Route:

```text
/analytics
```

Displays:

- Asset availability
- Maintenance completion
- Block utilization
- Block wastage
- Integrated-block percentage
- Unused block time
- Deferred tasks
- Train impact
- Department workload
- Planning accuracy
- Traditional vs RailBlock AI comparison

---

## Reports

Route:

```text
/reports
```

Supports:

- Operational reports
- Maintenance reports
- Block utilization reports
- Resource reports
- AI recommendation reports
- CSV export
- Print-friendly reports

---

## Administration

Route:

```text
/admin
```

Displays:

- Demo role
- Data-source status
- Model status
- Model performance
- System health
- Audit logs
- Configuration
- Synthetic data controls

---

# 23. No Login Requirement for Prototype

The prototype intentionally does **not require a login page**.

Role behaviour can be simulated through a Demo Role selector.

Example:

```text
Section Controller
DRM / Divisional Officer
Engineering Planner
TRD Planner
S&T Planner
Control Office Operator
Field Maintenance
Administrator
```

Authentication and enterprise RBAC can be integrated later.

---

# 24. Important Frontend Components

Reusable components include:

```text
KPI Card
Priority Badge
Department Badge
Status Badge
Railway Corridor Map
Track Segment
Train Marker
Block Marker
Maintenance Marker
Gantt Timeline
Conflict Indicator
Resource Card
AI Recommendation Card
XAI Explanation Drawer
Approval Bar
Alert Toast
Notification Centre
Filter Panel
Data Table
Modal
Confirmation Dialog
Audit Timeline
Simulation Panel
```

---

# 25. Backend

RailBlock AI uses a modular FastAPI backend.

## Technology Stack

```text
Python 3.11
FastAPI
Pydantic v2
Pandas
NumPy
scikit-learn
Google OR-Tools
WebSockets
Uvicorn
PostgreSQL
PostGIS
Redis
```

The backend is organized around API routes, service modules, intelligence engines, optimization, rescheduling, XAI, live operations, analytics, and audit services.

---

# 26. Backend Service Architecture

```text
backend/
└── app/
    ├── api/
    │   ├── dashboard
    │   ├── tasks
    │   ├── assets
    │   ├── spatial
    │   ├── scoring
    │   ├── blocks
    │   ├── planner
    │   ├── resources
    │   ├── execution
    │   ├── disruptions
    │   ├── xai
    │   ├── analytics
    │   └── realtime
    │
    ├── services/
    │   ├── ingestion
    │   ├── spatial
    │   ├── priority
    │   ├── clustering
    │   ├── optimization
    │   ├── rescheduler
    │   ├── xai
    │   ├── approval
    │   ├── live
    │   ├── audit
    │   └── analytics
    │
    └── models/
```

---

# 27. Backend Intelligence Pipeline

```text
Raw Data
   ↓
Ingestion
   ↓
Validation
   ↓
Normalization
   ↓
Unified Tasks
   ↓
Spatial Mapping
   ↓
MDPS Scoring
   ↓
Clustering
   ↓
Constraint Validation
   ↓
MILP Optimization
   ↓
XAI
   ↓
Block Recommendation
   ↓
Human Approval
```

---

# 28. Data Architecture

RailBlock AI uses synthetic but structurally realistic data because operational TMS, SMMS, TDMS, COA and BDMS datasets are not publicly available.

The prototype uses a named **New Delhi–Kanpur corridor** as the geographic demonstration corridor.

This provides a realistic spatial context while avoiding any claim that the dataset represents actual live Indian Railways operational data.

---

# 29. Raw Dataset Categories

```text
Network
Defects
Traffic
Resources
Historical
Disruptions
Calendars
```

---

# 30. Network Data

```text
stations.csv
block_sections.csv
track_geometry.csv
ohe_mast_reference.csv
signal_reference.csv
```

These datasets establish the spatial foundation.

---

# 31. Maintenance Data

```text
tms_defects.csv
smms_defects.csv
tdms_defects.csv
```

These represent maintenance requirements from:

```text
Engineering
TRD
S&T
```

---

# 32. Traffic Data

```text
train_timetable.csv
live_train_delays.csv
goods_forecast.csv
corridor_slot_availability.csv
```

These datasets provide:

- Passenger traffic
- Express traffic
- Freight traffic
- Delays
- Traffic density
- Available block windows

---

# 33. Resource Data

```text
machine_inventory.csv
crew_inventory.csv
```

These represent:

- Machines
- Maintenance gangs
- Department
- Location
- Shift
- Availability

---

# 34. Historical Data

```text
historical_block_records.csv
mdps_training_labels.csv
```

These support:

- MDPS model training
- Validation
- Historical block analysis
- Requested vs granted analysis
- Deferral analysis

---

# 35. Disruption Data

```text
disruption_events.csv
```

Represents:

```text
Late Train
Block Overrun
Emergency Defect
Machine Breakdown
```

---

# 36. Calendar Data

```text
seasonal_calendar.csv
festival_traffic_calendar.csv
```

Used to model changing operational conditions caused by:

- Monsoon
- Winter fog
- Summer
- Festivals
- Traffic peaks
- Seasonal maintenance urgency

---

# 37. Dataset Scale

The prototype is designed around a **minimum 25,000 maintenance-task-scale dataset** for meaningful UI, preprocessing, analytics and planning demonstrations.

The data generation pipeline should maintain:

- Referential integrity
- Unique identifiers
- Realistic distributions
- Temporal consistency
- Spatial consistency
- Department relationships
- Resource relationships
- Train/block relationships

The current frontend architecture is specifically prepared for large synthetic task datasets through pagination and derived-data optimization.

---

# 38. Data Processing Pipeline

Raw data is never directly modified.

```text
data/raw/
      ↓
Preprocessing
      ↓
data/processed/
      ↓
AI / Optimization
      ↓
data/outputs/
```

---

# 39. Processed Datasets

```text
unified_maintenance_tasks.csv
spatially_mapped_tasks.csv
scored_tasks.csv
clustered_tasks.csv
feasibility_checked_tasks.csv

enriched_train_traffic.csv
resource_availability.csv
planning_features.csv
```

---

# 40. Output Datasets

```text
weekly_block_plan.csv
monthly_rolling_block_plan.csv
disruption_reschedule_log.csv
rejected_block_requests.csv
planning_explanations.csv
```

---

# 41. Model Artifacts

```text
mdps_model.pkl
mdps_scaler.pkl
mdps_feature_metadata.json
rl_rescheduler_policy.pkl
model_metrics.json
```

Model artifacts should always be versioned and associated with the dataset/features used to produce them.

---

# 42. Data Generation Philosophy

Synthetic data should not simply be random numbers.

It must contain **relationships and operational patterns**.

For example:

```text
High Severity
     +
High Traffic
     +
Overdue
     +
Repeated Deferral
     ↓
High MDPS Score
```

Similarly:

```text
Spatially Close Tasks
     +
Compatible Time Windows
     +
Available Resources
     +
Compatible Departments
     ↓
Integrated Block Candidate
```

And:

```text
Train Delay
     +
Block Conflict
     ↓
Disruption
     ↓
Alternative Windows
     ↓
Constraint Validation
     ↓
Rescheduling Recommendation
```

---

# 43. Synthetic Data Disclaimer

RailBlock AI's prototype data is synthetic.

It is intended for:

- Demonstration
- Algorithm development
- UI development
- Testing
- Model experimentation
- Hackathon evaluation

It must **not** be represented as live Indian Railways operational data.

The frontend documentation likewise treats simulated AI, synthetic data, and live feeds explicitly as demonstration behaviour.

---

# 44. AI Architecture

RailBlock AI uses a hybrid intelligence architecture.

```text
                 RAILBLOCK AI
                      │
        ┌─────────────┼─────────────┐
        ↓             ↓             ↓
   MACHINE        DETERMINISTIC   OPTIMIZATION
   LEARNING          LOGIC
        │             │             │
        ↓             ↓             ↓
    MDPS Score    Constraints     MILP
    Risk Score    Spatial Logic   Scheduling
    Features      Validation      Allocation
        │             │             │
        └─────────────┼─────────────┘
                      ↓
                FINAL PLAN
```

This architecture deliberately avoids using machine learning as the sole scheduling mechanism.

---

# 45. Why Gradient Boosting?

Maintenance data is primarily tabular and contains nonlinear relationships between:

- Severity
- Overdue days
- Traffic density
- Deferrals
- Asset characteristics

Gradient Boosting is therefore appropriate for priority inference.

The backend currently implements a `GradientBoostingRegressor` for MDPS scoring.

---

# 46. Why OR-Tools?

Railway block scheduling involves hard constraints.

Examples:

```text
Cannot overlap occupied track section
Cannot schedule unavailable crew
Cannot schedule unavailable machine
Cannot violate block window
Cannot create conflicting train movement
```

A mathematical optimization solver is therefore more appropriate for the final schedule than unconstrained ML generation.

---

# 47. Why Deterministic Rescheduling?

Railway safety requires predictable behaviour.

The rescheduler may generate alternatives, but every proposed alternative must pass deterministic constraint validation before being presented as feasible.

This follows the backend's safety-first design principle.

---

# 48. Key Product User Flows

## Flow 1 — Task to Approval

```text
Dashboard
   ↓
Maintenance Task
   ↓
Task Explainability
   ↓
AI Recommendation
   ↓
Review
   ↓
Approve
```

---

## Flow 2 — AI Block Planning

```text
Planner
   ↓
Select Planning Horizon
   ↓
Generate AI Plan
   ↓
Cluster Tasks
   ↓
Optimize
   ↓
Review Timeline
   ↓
Inspect Conflicts
   ↓
Modify if required
   ↓
Approve
```

---

## Flow 3 — Live Disruption

```text
Live Monitor
   ↓
Train Delay
   ↓
Affected Block
   ↓
Disruption Console
   ↓
Generate Alternatives
   ↓
Simulate
   ↓
Select Option
   ↓
Apply Reschedule
   ↓
Audit Log
```

---

## Flow 4 — Maintenance Investigation

```text
Task Matrix
   ↓
Filter
   ↓
Select Task
   ↓
Priority Explanation
   ↓
Recommended Block
   ↓
Planner
```

---

## Flow 5 — Resource Planning

```text
Resource Dashboard
   ↓
Machine / Crew Availability
   ↓
Select Resource
   ↓
View Assignment
   ↓
View Block
   ↓
Validate Feasibility
```

These workflows correspond to the implemented frontend product flows.

---

# 49. Operational Status Model

RailBlock AI uses clear status categories.

```text
GREEN
Normal

AMBER
Warning / Maintenance

RED
Critical / Disruption
```

However, the interface must never depend on colour alone.

Every status should also contain:

```text
Icon + Text + Visual Indicator
```

---

# 50. Block Lifecycle

```text
DRAFT
  ↓
AI_RECOMMENDED
  ↓
PENDING_APPROVAL
  ↓
APPROVED
  ↓
SCHEDULED
  ↓
ACTIVE
  ↓
COMPLETED
```

Alternative:

```text
REJECTED
```

or:

```text
MODIFIED
  ↓
REVALIDATED
```

---

# 51. Auditability

Every significant decision should be auditable.

Example:

```text
Audit ID
Timestamp
User Role
Action
Entity ID
Previous Status
New Status
Rationale
```

The backend audit design records state mutations, approvals, modifications, rejections and rescheduling actions.

---

# 52. Analytics & Business Value

RailBlock AI measures improvement using operational KPIs.

## Core KPIs

### Block Utilization

```text
Actual Working Time
-------------------- × 100
Granted Block Time
```

### Asset Availability

```text
Available Operating Time
------------------------- × 100
Total Time
```

### Integration Rate

```text
Tasks included in multi-department blocks
------------------------------------------ × 100
Total planned tasks
```

### Deferred Task Rate

```text
Deferred Tasks
-------------- × 100
Total Tasks
```

### Train Impact

Measure:

- Delay minutes
- Number of affected trains
- Estimated disruption
- Recovery time

---

# 53. Before vs After Demonstration

The system should demonstrate:

```text
TRADITIONAL PLANNING
        VS
RAILBLOCK AI
```

Possible metrics:

| Metric | Traditional | RailBlock AI |
|---|---:|---:|
| Block Utilization | Lower | Higher |
| Asset Availability | Lower | Higher |
| Integrated Blocks | Low | Higher |
| Deferred Tasks | Higher | Lower |
| Unused Block Time | Higher | Lower |
| Train Impact | Higher | Lower |
| Planning Time | Higher | Lower |

> All numerical improvement values shown in the prototype must be clearly labelled as **synthetic simulation results**, not measured Indian Railways production results.

---

# 54. Project Folder Structure

```text
railblock-ai/
│
├── frontend/
│
├── backend/
│
├── data/
│   ├── raw/
│   │   ├── network/
│   │   ├── defects/
│   │   ├── traffic/
│   │   ├── resources/
│   │   ├── historical/
│   │   ├── disruptions/
│   │   └── calendars/
│   │
│   ├── processed/
│   ├── outputs/
│   ├── models/
│   └── generators/
│
├── notebooks/
│
├── docs/
│   ├── data_dictionary.md
│   ├── data_sources.md
│   ├── architecture.md
│   └── api.md
│
├── README.md
└── .gitignore
```

---

# 55. Data Folder

```text
data/
├── raw/
├── processed/
├── outputs/
├── models/
└── generators/
```

### Raw

Original synthetic input data.

### Processed

Cleaned and transformed datasets.

### Outputs

Generated planning results.

### Models

Trained model artifacts.

### Generators

Reproducible synthetic-data generation scripts.

---

# 56. Reproducibility

All synthetic data generation should be deterministic when a fixed random seed is supplied.

Example:

```text
SEED = 42
```

The same configuration should generate the same dataset.

This is important for:

- Debugging
- Testing
- Model comparison
- Hackathon demonstrations
- Reproducibility

---

# 57. Data Integrity Requirements

Every generated dataset must maintain:

### Unique IDs

```text
task_id
section_id
station_code
resource_id
crew_id
block_id
event_id
```

### Referential Integrity

For example:

```text
tms_defects.section_id
        ↓
block_sections.section_id
```

```text
smms_defects.signal_id
        ↓
signal_reference.signal_id
```

```text
tdms_defects.mast_number
        ↓
ohe_mast_reference.mast_number
```

---

# 58. Security & Governance

The production architecture should eventually support:

- JWT authentication
- Role-based access control
- Division-level permissions
- Audit trails
- API authentication
- Secure WebSockets
- Input validation
- Rate limiting
- Data encryption
- Secure model management

The current prototype may use simulated/demo roles while remaining architecturally ready for enterprise authentication.

---

# 59. Real-Time Architecture

```text
COA / Telemetry Simulation
          ↓
     WebSocket
          ↓
Backend Realtime Service
          ↓
Frontend Live Monitor
          ↓
Disruption Detection
          ↓
Rescheduler
          ↓
Alternative Plan
```

The current backend exposes a WebSocket-based simulated live stream for operational telemetry.

---

# 60. Performance Strategy

The product is designed primarily for desktop control-room workstations.

Important performance strategies include:

- Pagination for large task tables
- Memoized derived calculations
- Route-level code splitting
- Limited DOM rendering
- Efficient conflict calculations
- Asynchronous optimization jobs where required
- WebSocket streaming rather than continuous polling
- Cached derived analytics

The frontend architecture specifically uses pagination for the large task dataset and code splitting for heavy routes.

---

# 61. Accessibility

The frontend should support:

- Semantic HTML
- Keyboard navigation
- Visible focus states
- Accessible labels
- Screen-reader friendly controls
- Icon + text status indicators
- Keyboard command palette
- Clear error messages

Status must never depend exclusively on colour.

---

# 62. Testing Strategy

## Frontend

```text
Unit Tests
Component Tests
Integration Tests
Route Smoke Tests
E2E Tests
```

Important test areas:

```text
Priority display
Conflict detection
Planner drag/resize
Approval workflow
Recommendation modification
Disruption simulation
Analytics
```

---

## Backend

Test:

```text
Data validation
Spatial translation
MDPS prediction
Clustering
Constraint validation
Optimization
Approval transitions
Rescheduling
XAI
Audit logging
API endpoints
WebSockets
```

---

# 63. Development Phases

## Phase 1 — Data Foundation

```text
Generate synthetic data
↓
Validate datasets
↓
Establish referential integrity
```

---

## Phase 2 — Backend Intelligence

```text
Ingestion
↓
Spatial Translation
↓
MDPS
↓
Clustering
↓
Constraints
↓
Optimization
```

---

## Phase 3 — Frontend

```text
Command Dashboard
↓
Planner
↓
Tasks
↓
Resources
↓
XAI
↓
Live Operations
↓
Disruptions
↓
Analytics
```

---

## Phase 4 — Integration

```text
Frontend
   ↕
REST API
   ↕
Backend
   ↕
Data / Models
```

---

## Phase 5 — Validation

```text
Unit Tests
↓
Integration Tests
↓
Scenario Tests
↓
Performance Tests
↓
End-to-End Demo
```

---

# 64. Demonstration Scenario

A strong demonstration should follow a realistic operational scenario.

### Step 1

Open Command Dashboard.

Show:

```text
Critical Defects
Overdue Tasks
Active Blocks
Traffic Conditions
Asset Availability
```

### Step 2

Open Maintenance Matrix.

Filter:

```text
Severity = Critical
Status = Pending
```

### Step 3

Open a high-priority task.

Show:

```text
MDPS = 94
```

and explain why.

### Step 4

Open AI Block Planner.

Generate an AI plan.

### Step 5

Show:

```text
Engineering
+
TRD
+
S&T
```

being consolidated into one integrated block.

### Step 6

Show:

```text
Train impact
Resource availability
Constraint validation
Block utilization
```

### Step 7

Approve the block.

### Step 8

Open Live Monitor.

Inject a train delay.

### Step 9

Open Self-Healing Console.

Show:

```text
Original Plan
vs
Alternative Plans
```

### Step 10

Apply the selected reschedule.

### Step 11

Open Analytics.

Show:

```text
Traditional Planning
vs
RailBlock AI
```

### Step 12

Open Audit Log.

Show the complete decision history.

---

# 65. What Makes RailBlock AI Different?

RailBlock AI is not simply:

```text
Dashboard + ML Model
```

It combines:

```text
Spatial Intelligence
        +
Maintenance Risk Intelligence
        +
Shadow Block Consolidation
        +
Resource Intelligence
        +
Constraint Optimization
        +
Explainable AI
        +
Human Approval
        +
Live Monitoring
        +
Self-Healing Rescheduling
        +
Auditability
```

This combination transforms the system from a basic maintenance dashboard into a **railway operations decision-support platform**.

---

# 66. Safety Position

RailBlock AI is a decision-support system.

It does **not** directly control:

- Signals
- Interlocking
- Points
- Train movement
- Track circuits
- Railway signalling hardware

AI-generated plans are recommendations.

Human railway authorities remain responsible for operational approval and execution.

---

# 67. Prototype Scope

The current prototype focuses on:

```text
Synthetic Data
New Delhi–Kanpur Demonstration Corridor
Maintenance Block Planning
Multi-Department Integration
AI Priority Scoring
Constraint-Based Scheduling
Resource Feasibility
Explainable Recommendations
Simulated Live Operations
Self-Healing Rescheduling
Analytics
Auditability
```

It is not intended to represent a live deployment into Indian Railways operational infrastructure.

---

# 68. Future Production Roadmap

## Priority 1 — Enterprise Authentication

Integrate:

```text
JWT
RBAC
Active Directory / Enterprise Identity
Division-level permissions
```

---

## Priority 2 — Live Railway Data

Replace simulated feeds with approved integrations for:

```text
COA
TMS
SMMS
TDMS
BDMS
FOIS
```

---

## Priority 3 — Production Spatial Infrastructure

Deploy:

```text
PostgreSQL
+
PostGIS
+
Railway Digital Twin
```

---

## Priority 4 — Distributed Optimization

For multiple divisions:

```text
FastAPI
+
Redis
+
Celery
+
Optimization Workers
```

---

## Priority 5 — Reinforcement Learning

Train rescheduling policies in controlled simulation environments.

The production roadmap should retain deterministic hard-constraint validation even when RL is introduced. This is consistent with the project's safety-first architecture.

---

# 69. Expected Long-Term Impact

If deployed with validated railway operational data, RailBlock AI aims to help Indian Railways:

### Improve

- Asset availability
- Maintenance coordination
- Block utilization
- Resource utilization
- Planning visibility
- Operational resilience

### Reduce

- Unnecessary blocks
- Maintenance deferrals
- Block wastage
- Resource idle time
- Train disruption
- Manual planning effort

---

# 70. Project Success Metrics

The product should ultimately be evaluated using measurable operational KPIs:

```text
↑ Asset Availability

↑ Block Utilization

↑ Integrated Block Percentage

↑ Maintenance Completion Rate

↓ Deferred Maintenance

↓ Unused Block Time

↓ Train Delay Impact

↓ Planning Time

↓ Resource Conflicts

↑ Schedule Stability
```

All prototype metrics must be identified as simulated unless validated against real operational data.

---

# 71. Key Product Components

```text
                    RAILBLOCK AI
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   DATA LAYER       AI LAYER        OPERATIONS LAYER
        │                │                │
    TMS/SMMS          MDPS            Planner
    TDMS/COA          Spatial          Live Monitor
    BDMS              Clustering       Resources
    Synthetic         XAI              Disruptions
    Data              Optimization     Approval
                      Rescheduler       Analytics
```

---

# 72. Product Positioning

### One-line description

> **RailBlock AI is an AI-powered railway operations decision-support platform that automatically identifies, prioritizes, consolidates, validates, and optimizes maintenance blocks while minimizing their impact on train operations.**

### Short pitch

> RailBlock AI transforms fragmented railway maintenance planning into an integrated, spatially intelligent and constraint-aware planning process. It combines AI-based maintenance prioritization, multi-department shadow-block consolidation, resource-aware optimization, explainable recommendations and self-healing rescheduling to maximize asset availability while keeping human railway controllers in control.

---

# 73. Final Product Vision

The long-term vision of RailBlock AI is to become an intelligent planning layer for railway infrastructure maintenance.

```text
                  EXISTING SYSTEMS

       TMS   SMMS   TDMS   COA   BDMS
        │     │      │     │      │
        └─────┴──────┴─────┴──────┘
                     │
                     ▼
              ┌──────────────┐
              │ RAILBLOCK AI  │
              └──────────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
    PRIORITIZE   OPTIMIZE    MONITOR
        │            │            │
        └────────────┼────────────┘
                     ▼
              RECOMMENDED PLAN
                     │
                     ▼
              HUMAN APPROVAL
                     │
                     ▼
             EXECUTABLE BLOCK
                     │
                     ▼
              LIVE MONITORING
                     │
                     ▼
             SELF-HEALING PLAN
```

The ultimate objective is:

> **More maintenance completed in fewer, better-utilized blocks — with fewer conflicts, less train disruption, better resource utilization, and higher railway asset availability.**

---

# 74. Repository Documentation

The repository should maintain detailed documentation in:

```text
docs/
├── architecture.md
├── api.md
├── data_dictionary.md
├── data_sources.md
└── deployment.md
```

Component-specific documentation should remain inside:

```text
frontend/README.md
backend/README.md
data/README.md
```

The root README remains the **product-level source of truth**, while subsystem READMEs document their individual implementation details.

---

# 75. Current Architecture Status

The backend has been designed as a modular decision-support system with:

- FastAPI APIs
- Spatial translation
- MDPS priority scoring
- Spatial clustering
- Deterministic constraint validation
- OR-Tools optimization
- XAI
- Approval workflow
- Live simulation
- Disruption handling
- Audit logging
- Analytics

The existing backend documentation reports a staging-ready prototype with automated testing and the major intelligence pipeline implemented.

The frontend specification provides the corresponding command-centre UI, planning workflows, task analysis, resource monitoring, disruption handling and analytics surfaces.

---

# 76. Final Architecture Summary

```text
                         RAILBLOCK AI
                              │
                              ▼
                     DATA INGESTION LAYER
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
             TMS             TDMS            SMMS
              │               │               │
              └───────────────┼───────────────┘
                              │
                             COA
                              │
                              ▼
                    DATA NORMALIZATION
                              │
                              ▼
                  GEO-SPATIAL TRANSLATOR
                              │
                              ▼
                 UNIFIED MAINTENANCE TASKS
                              │
                              ▼
                    MDPS PRIORITY ENGINE
                              │
                              ▼
                  SHADOW-BLOCK CLUSTERING
                              │
                              ▼
                 RESOURCE FEASIBILITY ENGINE
                              │
                              ▼
                  HARD CONSTRAINT VALIDATION
                              │
                              ▼
                    OR-TOOLS OPTIMIZATION
                              │
                              ▼
                    AI RECOMMENDATION
                              │
                              ▼
                     XAI EXPLANATION
                              │
                              ▼
                     HUMAN CONTROLLER
                       │             │
                    APPROVE      MODIFY/REJECT
                       │
                       ▼
                  SCHEDULED BLOCK
                       │
                       ▼
                 LIVE MONITORING
                       │
                       ▼
                 DISRUPTION DETECTION
                       │
                       ▼
              SELF-HEALING RESCHEDULER
                       │
                       ▼
                CONSTRAINT VALIDATION
                       │
                       ▼
                ALTERNATIVE PLAN
                       │
                       ▼
                  HUMAN APPROVAL
                       │
                       ▼
                 UPDATED BLOCK PLAN
                       │
              ┌────────┴─────────┐
              ▼                  ▼
         AUDIT LOG           ANALYTICS
```

---

# 77. Final Statement

**RailBlock AI is designed to move railway maintenance planning from fragmented, manually coordinated block requests toward intelligent, integrated and explainable decision support.**

Instead of asking:

> **"Which department gets a block?"**

RailBlock AI asks:

> **"What maintenance is most urgent, which activities can safely be combined, when can they be completed with the least operational impact, are the required resources available, and how should the plan adapt when railway conditions change?"**

That is the core intelligence behind RailBlock AI.

---

## Project Identity

**Product:** RailBlock AI  
**Domain:** Railway Operations & Maintenance  
**Problem Statement:** SIH 26027  
**Primary Objective:** Maximize railway asset availability through intelligent maintenance block planning  
**Demonstration Corridor:** New Delhi–Kanpur  
**Architecture:** AI + Deterministic Constraints + Mathematical Optimization + Human-in-the-Loop  
**Data:** Synthetic, structurally realistic demonstration data  
**Frontend:** React + TypeScript  
**Backend:** FastAPI + Python  
**Optimization:** Google OR-Tools  
**ML:** Gradient Boosting  
**Spatial Intelligence:** Linear Referencing / PostGIS-ready architecture  
**Realtime:** WebSocket-based simulated telemetry  
**Governance:** Human approval + Audit Trail