# RailBlock AI — Frontend ↔ Backend Integration Reference

> **Last Updated**: 2026-08-28  
> **Integration Status**: Fully wired — API clients, stores, pages, and WebSocket stream connected.

---

## Overview

RailBlock AI integrates a **FastAPI backend** (Python, OR-Tools, GradientBoostingRegressor ML, `uvicorn`) with a **React + TypeScript + Vite frontend** (Zustand stores, Recharts, Leaflet). This document is the single reference for the complete integration contract.

```
Frontend (React/Vite)             Backend (FastAPI/uvicorn)
═══════════════════════           ════════════════════════════
Zustand Stores ──────── REST ──►  /api/{domain}/{route}
WebSocket Client ─── WS ──────►  /ws/{endpoint}
```

---

## Environment Configuration

| Variable | Frontend File | Value |
|---|---|---|
| `VITE_API_BASE_URL` | `frontend/.env` | `http://localhost:8000/api` |
| `VITE_WS_BASE_URL` | `frontend/.env` | `ws://localhost:8000` |

---

## API Layer Architecture

All API clients live in `frontend/src/api/`. The central HTTP client is [`client.ts`](../frontend/src/api/client.ts).

### Domain API Modules

| Module | File | Backend Routes |
|---|---|---|
| **Tasks** | `tasksApi.ts` | `GET /tasks`, `GET /tasks/{id}`, `GET /tasks/{id}/priority`, `POST /tasks/unify` |
| **Planner** | `plannerApi.ts` | `POST /planner/optimize`, `GET /planner/weekly`, `GET /planner/monthly`, `GET /planner/rolling`, `POST /planner/simulate` |
| **Blocks** | `blocksApi.ts` | `GET /blocks`, `GET /blocks/{id}`, `POST /blocks/candidates`, `POST /blocks/generate`, `POST /blocks/check-feasibility`, `POST /blocks/{id}/approve`, `POST /blocks/{id}/modify`, `POST /blocks/{id}/reject`, `POST /blocks/{id}/execute` |
| **Execution** | `executionApi.ts` | `GET /execution/active`, `GET /execution/metrics`, `GET /execution/section-modifier/{section_id}`, `POST /blocks/{id}/execute` |
| **Seasonal** | `seasonalApi.ts` | `GET /seasonal/context/{section_id}`, `GET /seasonal/sections`, `GET /seasonal/live/{section_id}` |
| **Disruptions** | `disruptionsApi.ts` | `GET /disruptions`, `POST /disruptions/detect`, `POST /disruptions/reschedule`, `POST /disruptions/approve` |
| **XAI** | `xaiApi.ts` | `GET /xai/explain/{block_id}` |
| **Scoring** | `scoringApi.ts` | `POST /scoring/priority`, `POST /scoring/train` |
| **Resources** | `resourcesApi.ts` | `GET /resources`, `GET /resources/crew`, `GET /resources/live` |
| **Analytics** | `analyticsApi.ts` | `GET /analytics/overview`, `GET /analytics/impact`, `GET /analytics/department-workload`, `GET /audit` |
| **System** | `systemApi.ts` | `GET /system/health`, `GET /system/data-status`, `POST /system/validate-data`, `GET /auth/status` |
| **Live** | `liveApi.ts` | `GET /live/trains`, `GET /live/status`, `POST /live/sync` |
| **WebSocket** | `websocketClient.ts` | `ws://localhost:8000/ws/live`, `ws://localhost:8000/ws/blocks` |

---

## Store → API Integration Map

### `taskStore.ts`
- **Data source**: `getAllTasks()` (local synthetic data, 150 tasks seeded from MDPS)
- **Integration**: `tasksApi.ts` available for `GET /tasks` enrichment — call `tasksApi.getTasks()` in components as needed.
- **Pattern**: Local-first; backend is authoritative source for priority scores.

### `plannerStore.ts`
- **Block approval** → `blocksApi.approveBlock(id, payload)` (async, fire-and-forget with graceful fallback)
- **Block rejection** → `blocksApi.rejectBlock(id, payload)` (async)
- **Block modification** → `blocksApi.modifyBlock(id, payload)` (async)
- **AI generation** → `plannerApi.runOptimization()` fired in parallel with local `generateAIPlan()` simulation
- **Pattern**: Optimistic UI update first, backend persistence second.

### `disruptionStore.ts`
- **`ensureOptions(eventId)`**: Generates local options immediately, then replaces with backend constraint-validated options from `disruptionsApi.rescheduleBlock()`.
- **`applyReschedule(eventId)`**: Applies locally + calls `disruptionsApi.approveReschedule()` to persist.
- **Pattern**: Two-phase — local fast response + backend validation overlay.

### `resourceStore.ts`
- **`fetchResources()`**: Calls `resourcesApi.getMachines()` and `resourcesApi.getCrews()` to overlay live availability and utilization onto locally-seeded resources.
- **Pattern**: Availability enrichment — does NOT replace local data, only patches fields backend has.

### `operationsStore.ts`
- **`initLiveStream()`**: Fetches initial train positions from `liveApi.getTrainPositions()`, then subscribes to `ws://localhost:8000/ws/live` via `liveTrainSocket`.
- **Simulation fallback**: Continues local simulation ticking even when WebSocket is unavailable.
- **Pattern**: Hybrid — WebSocket live data overlays simulation ticking.

---

## Page → API Integration Map

| Page | File | Backend Integration |
|---|---|---|
| **Dashboard** | `DashboardPage.tsx` | Reads from plannerStore (blocks count), operationsStore (train positions) |
| **Live Corridor** | `LiveCorridorPage.tsx` | `initLiveStream()` on mount → WS `/ws/live`; HTTP fallback `/live/trains` |
| **Planner** | `PlannerPage.tsx` | Block approve/reject/modify → `blocksApi.*`; AI generation → `plannerApi.runOptimization()` |
| **Disruptions** | `DisruptionsPage.tsx` | `ensureOptions()` → `disruptionsApi.rescheduleBlock()`; apply → `disruptionsApi.approveReschedule()` |
| **Analytics** | `AnalyticsPage.tsx` | `analyticsApi.getOverviewKPIs()` for live KPI row; falls back to local computed KPIs |
| **Admin** | `AdminPage.tsx` | `systemApi.getHealth()`, `systemApi.getDataStatus()`, `systemApi.validateData()`, `analyticsApi.getAuditLogs()` |
| **Tasks** | `TaskListPage.tsx` | Local store with `tasksApi.*` available for enrichment |
| **Recommendations** | `RecommendationsPage.tsx` | AI recommendations from local plannerStore; XAI via `xaiApi.explainBlock()` |

---

## WebSocket Event Protocol

### `/ws/live` — Train Telemetry
```json
{
  "event_type": "TRAIN_POSITION_UPDATED",
  "timestamp": "2026-08-28T07:30:00Z",
  "source": "LiveTrainProvider",
  "data": [
    {
      "train_id": "12622",
      "section_id": "MAS-AJJ",
      "current_km": 35.2,
      "speed_kmph": 92.5,
      "delay_minutes": 8
    }
  ]
}
```

### `/ws/blocks` — Block Status Updates
```json
{
  "event_type": "BLOCK_STATUS_CHANGED",
  "timestamp": "2026-08-28T07:31:00Z",
  "data": {
    "block_id": "RB-402",
    "status": "APPROVED",
    "approved_by": "Controller"
  }
}
```

---

## Request/Response Schema Contracts

### Block Approval — `POST /blocks/{id}/approve`

**Request**:
```json
{
  "approved_by": "Section Controller",
  "role": "Controller",
  "notes": "Optional notes"
}
```

**Response**:
```json
{
  "status": "approved",
  "block_id": "RB-402",
  "approved_by": "Section Controller"
}
```

---

### Disruption Reschedule — `POST /disruptions/reschedule?event_id=EVT-9001&affected_block_id=RB-402`

**Request body** (optional metadata):
```json
{
  "section_id": "MAS-AJJ",
  "criticality_score": 85.0,
  "duration_minutes": 180
}
```

**Response**:
```json
{
  "status": "success",
  "request_id": "...",
  "engine_version": "v2.1",
  "scoring_mode": "deterministic",
  "options": [
    {
      "option_id": "OPT-001",
      "action_type": "delay",
      "proposed_start_time": "2026-08-28 02:30:00",
      "proposed_end_time": "2026-08-28 05:30:00",
      "duration_minutes": 180,
      "optimization_score": 0.92,
      "feasible": true,
      "failed_constraints": [],
      "reason": "Shifted by 1h to avoid peak traffic"
    }
  ],
  "approval_required": true
}
```

---

### System Health — `GET /system/health`

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2026-08-28T07:30:00Z",
  "data_sources": {
    "tasks": { "status": "loaded", "row_count": 150 },
    "trains": { "status": "loaded", "row_count": 42 }
  },
  "ai_engines": {
    "mdps": { "available": true, "model_type": "GradientBoostingRegressor", "version": "1.0" }
  }
}
```

---

## Error Handling Strategy

All API calls follow a **graceful degradation** pattern:

1. **Optimistic UI first** — stores apply state changes locally before backend confirms.
2. **Silent fallback** — all `.catch(() => {})` blocks preserve local state when backend is unavailable.
3. **No error modals** — backend errors do not crash the UI; local simulation continues.
4. **Backend as enrichment layer** — backend data supplements, not replaces, seeded local data.

---

## Authentication & Governance

Backend implements a **prototype stub** at `GET /api/auth/status` returning `{ "status": "mock", "message": "No real auth" }`.

> **No JWT or complex session service is implemented** in this prototype. The active operator role is managed within `settingsStore` and dynamically supplied to approval/rejection endpoints to maintain audit trail integrity. The demo role UI selector was removed to keep the operations console focused and uncluttered.

---

## Running the Full Stack

### Start Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Start Frontend
```bash
cd frontend
npm install
npm run dev
```

Frontend dev server runs at `http://localhost:5173`.  
Backend API available at `http://localhost:8000/api`.  
Interactive API docs at `http://localhost:8000/docs`.

---

## Test Validation Commands

```bash
# Backend: must pass 143/143 tests
cd backend && python -m pytest tests/ -v

# Frontend: must build with 0 errors
cd frontend && npm run build

# Frontend: TypeScript strict check
cd frontend && npx tsc --noEmit
```
