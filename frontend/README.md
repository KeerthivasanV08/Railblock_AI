# RailBlock AI Frontend

## 1. Project Overview

RailBlock AI is an AI-assisted **Railway Operations Command Centre** for maintenance block planning,
conflict detection, resource optimisation and self-healing rescheduling on the canonical **Chennai –
Thoothukudi** corridor. This repository contains the **frontend application** — a React/TypeScript
interface powered by domain-grounded corridor state and REST/WebSocket API integration with the FastAPI backend (`analyticsApi`, `seasonalApi`, `plannerApi`, `tasksApi`, `disruptionsApi`, `executionApi`). Target users are control-office operators, section controllers, divisional officers and Engineering/TRD/S&T planners.

## 2. Product Goals

- Consolidate maintenance tasks from TMS / SMMS / TDMS / COA into one prioritised, spatially aware view.
- Cluster spatially/temporally compatible tasks into **integrated blocks** and recommend them via a
  local AI Simulation.
- Detect conflicts (train overlaps, block overlaps, resource unavailability) before they become
  operational incidents.
- Support an end-to-end approval workflow (draft → AI recommended → pending approval → approved →
  scheduled → active → completed, or rejected).
- Provide real-time (simulated) corridor awareness and a self-healing rescheduling console for
  disruptions.
- Demonstrate measurable value through before/after analytics.

## 3. Frontend Architecture

| Layer                  | Choice                                                                                             | Why                                                                                                                                                                          |
| ---------------------- | -------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Framework              | React 19 + TypeScript (strict)                                                                     | Type-safe, componentised UI                                                                                                                                                  |
| Build                  | Vite + TanStack Start (file-based SSR-capable router)                                              | Fast dev loop; file routing scales with the number of pages                                                                                                                  |
| Routing                | `@tanstack/react-router` file routes                                                               | Type-safe params, nested layouts (`_app` pathless layout wraps every page in the shell)                                                                                      |
| UI kit                 | Tailwind CSS v4 + shadcn/ui (Radix primitives)                                                     | Accessible primitives, full control of the dark command-centre theme                                                                                                         |
| State                  | Zustand                                                                                            | Small, explicit stores per domain, no boilerplate                                                                                                                            |
| Server-state           | TanStack Query (`QueryClientProvider` wired in `__root.tsx`)                                       | Ready for real API/WebSocket integration later                                                                                                                               |
| Forms                  | React Hook Form + Zod                                                                              | Validated Modify Block / Modify Recommendation forms                                                                                                                         |
| Charts                 | Recharts                                                                                           | Analytics trend lines & bars                                                                                                                                                 |
| Corridor visualisation | Custom SVG (`CorridorMap`)                                                                         | MapLibre/tile services need network + API keys unavailable in this environment; the SVG corridor is the explicit "graceful fallback" the spec allows and never renders blank |
| Icons                  | lucide-react                                                                                       | Consistent icon language for status semantics                                                                                                                                |
| Dates                  | small local `dateUtils` helpers (minute-of-day based, since the planner works in intraday minutes) |

## 4. Application Structure (Routes)

```
/                                → redirects to /dashboard
/dashboard                       → Command Dashboard
/live                            → Live Corridor Monitor
/planner                         → AI Block Planner
/tasks                           → Maintenance Task Matrix
/tasks/:taskId                   → Task Explainability
/recommendations                 → AI Recommendations / XAI Console
/recommendations/:recommendationId
/resources                       → Resource Availability
/disruptions                     → Self-Healing Console
/disruptions/:eventId
/analytics                       → Analytics
/reports                         → Reports
/admin                           → Administration
```

All routes above `/` live under the pathless `routes/_app.tsx` layout, which renders `<AppShell>`
(sidebar + header + command palette + toaster) once and an `<Outlet/>` for the page.

> **Note on `routeTree.gen.ts`**: this file is normally auto-generated by the TanStack Router Vite
> plugin whenever you run `npm run dev` or `npm run build`. It was regenerated **by hand** here because
> this environment has no network access to install dependencies and run the codegen CLI. The moment you
> run `npm install && npm run dev`, the plugin will re-run codegen and overwrite it with a verified copy
> — this is expected and safe.

## 5. Page-by-Page Explanation

- **Command Dashboard** (`/dashboard`) — KPI strip (asset availability, active blocks, critical
  defects, overdue tasks, utilisation, integrated blocks, potential time saved, pending approvals), the
  corridor map, and six clickable operational panels (Upcoming Blocks, Train Delays, Critical
  Maintenance, AI Insights, Disruption Alerts).
- **Live Corridor Monitor** (`/live`) — simulated live feed: trains move along the corridor every tick,
  play/pause/speed controls, resource/crew/disruption status panels. Occasionally raises a **Train
  Delay** notification and, past a threshold, injects a new disruption event.
- **AI Block Planner** (`/planner`) — the primary workstation: a 7-lane Gantt-style timeline
  (Passenger/Express/Freight/Engineering/TRD/S&T/Integrated), draggable & resizable blocks, conflict
  highlighting, a right-hand Block Detail panel (approve/reject/modify/lock/unlock/simulate), **Generate
  AI Plan** (staged progress overlay → clusters pending tasks → proposes integrated blocks) and
  **Compare Plans** (current vs AI plan metrics).
- **Maintenance Task Matrix** (`/tasks`) — dense, filterable, paginated table over the 25,000-task
  synthetic dataset (department / severity / status / priority / overdue / recommended / search).
- **Task Explainability** (`/tasks/:taskId`) — priority-score breakdown bars, natural-language AI
  explanation, defect history, related planning info, and a "View Recommended Block" jump into the
  planner.
- **AI Recommendations / XAI Console** (`/recommendations`, `/recommendations/:id`) — recommendation
  cards/detail with "why recommended" reasons, factor bars, and Approve / Modify (validated form) /
  Reject / Simulate actions, all wired to the planner's block state.
- **Resource Availability** (`/resources`) — machines & crew tables, a resource calendar
  (Mon–Fri availability bars), and a corridor map of machine positions.
- **Self-Healing Console** (`/disruptions`, `/disruptions/:eventId`) — disruption list; detail view
  with AI-generated reschedule options (RL Rescheduler simulation), Simulate (before/after comparison)
  and Apply Reschedule (mutates the affected block and logs an audit event).
- **Analytics** (`/analytics`) — KPI tiles, 7 Recharts trend/bar charts, department workload, and a
  Traditional Planning vs RailBlock AI before/after table.
- **Reports** (`/reports`) — report cards by category with CSV export and a print-friendly view.
- **Administration** (`/admin`) — Demo Role selector, data-source/model/system health status, and the
  live audit log.

## 6. User Flows

- **Flow A**: Dashboard → Task → Explainability → Recommendation → Approval
- **Flow B**: Dashboard → Planner → Generate AI Plan → Review → Modify → Approve
- **Flow C**: Live Monitor → Train Delay → Disruption → Simulate → Reschedule
- **Flow D**: Task Matrix → Filter → Task Detail → Recommended Block → Planner
- **Flow E**: Resources → Availability → Block → Assignment

All five flows are implemented end-to-end with real state changes, toasts and audit-log entries.

## 7. AI Simulation

Everything labelled **AI Simulation** in the UI is a deterministic, explainable local computation —
there is no call to a real model:

- **Priority scoring** (`utils/scoring.ts`) — `priority = severity + overdue_risk + traffic_impact +
asset_criticality + deferral_risk`, normalised to 0–100, with a natural-language `explainPriority()`.
- **AI plan generation** (`services/mock/aiService.ts: generateAIPlan`) — clusters spatially/temporally
  compatible pending tasks, searches the intraday window for the lowest-traffic slot, and derives
  utilisation / train impact / confidence from real inputs (task count, department mix, traffic clashes).
- **Conflict detection** (`utils/conflictDetection.ts`) — checks train-path overlap, block-block overlap,
  machine/crew availability and window overflow, each with suggested alternative windows.
- **Resource feasibility** (`checkResourceAvailability`) — matches a task's required resource type
  against currently available machines/crew.
- **Self-healing rescheduling** (`generateRescheduleOptions`) — proposes three alternative windows with
  computed train/maintenance/resource impact and confidence.

The frontend does **not** connect to any real AI/ML service.

## 8. Mock Data

All synthetic data lives under `src/data/`:

- `stations.ts`, `sections.ts` — the 9-station, 8-section NDLS–CNB corridor (km-anchored).
- `trains.ts` — ~14 Passenger/Express/Freight trains and their intraday paths.
- `tasks.ts` — the 25,000-row maintenance task dataset (deterministic PRNG, realistic defects per
  department, priority computed via `utils/scoring.ts`).
- `resources.ts` — machines (tampers, ballast cleaners, tower wagons, rail grinders, inspection
  vehicles) and crews.
- `operations.ts` — seeded blocks, AI recommendations, disruptions, notifications and audit log for the
  built-in demo scenario, plus `PLAN_DATE`/`PLAN_START_MIN`/`PLAN_END_MIN`.
- `analytics.ts` — KPI, trend, department-workload, before/after and report definitions for the
  Analytics and Reports pages.

All generators use a seeded `mulberry32` PRNG (`lib/random.ts`) so the dataset is stable across renders.

## 9. State Management (Zustand stores, `src/stores/`)

- `taskStore` — the task dataset, filters, pagination.
- `plannerStore` — blocks, train paths, AI generation staging, approve/reject/modify/lock/move/resize,
  compare-plan baseline.
- `recommendationStore` — AI recommendations; approve/reject/modify also update the linked block in
  `plannerStore`.
- `disruptionStore` — disruption events, generated reschedule options, simulation results, apply.
- `operationsStore` — live train positions/ticking, play/pause/speed, and occasional delay injection.
- `resourceStore` — machines & crew, availability/assignment.
- `notificationStore` — notifications + audit log (`push`, `logAudit`, `markRead`, `clearAll`).
- `settingsStore` — Demo Role, sidebar collapse, command-palette open state.

## 10. Component Architecture

`src/components/` is organised by domain (`layout`, `common`, `map`, `planner`, `tasks`,
`recommendations`, `resources`, `disruptions`, `analytics`, `reports`, `admin`, `dashboard`) plus a
shared shadcn/ui primitive layer in `components/ui`. Reusable primitives include `StatusBadge` /
`DomainBadges` (severity, department, priority, AI), `KPICard`, `PageHeader`, `States` (loading / empty /
error), and `ConfirmDialog`.

## 11. Map Architecture

`components/map/CorridorMap.tsx` renders the corridor as an SVG line with station ticks, and layered,
toggleable entities (stations, trains with direction arrows, blocks as lane-coloured bands, critical
defects, machines). This is a deliberate, self-contained fallback in place of MapLibre GL — the brief
explicitly allows a stylised fallback when external tiles/API keys are unavailable, which is the case in
this offline build environment. It is reused across the Dashboard, Live Corridor and Resources pages
with different entity sets, and is structured so a MapLibre-backed implementation could be swapped in
behind the same props later.

## 12. Timeline Architecture

`components/planner/PlannerTimeline.tsx` is a custom Gantt built with absolutely-positioned divs over a
06:00–20:00 minute-scale grid (no external Gantt library, per the "one primary timeline approach"
requirement). It supports pointer-driven drag-to-move and drag-to-resize (15-minute snapping), a
current-time indicator, thin reference bars for train paths, and a red ring for any block with an active
conflict (computed live via `utils/conflictDetection.ts`).

## 13. Responsive Design

The shadcn `Sidebar` collapses to icons on smaller viewports and via the header trigger; KPI grids and
chart grids collapse from 8/4/2 → 1 column; the task table scrolls horizontally; the planner timeline
scrolls both directions. Primary optimisation target is a desktop control-room workstation, as required.

## 14. Accessibility

Semantic landmarks (`header`, `nav`, `main`, `aside`), keyboard-operable command palette (`Ctrl/Cmd+K`),
focus-visible states from the shadcn/Radix primitives, `aria-label`s on icon-only buttons, and status
never conveyed by colour alone (every badge pairs an icon + text label).

## 15. Performance

- The 25,000-row task dataset is paginated (25/page) rather than fully rendered — see `taskStore`.
- Analytics/derived values are computed with `useMemo` where they depend on large arrays.
- Conflict detection runs once per render over the (small) active block set, not per row.
- Heavy pages are plain route-level code-split automatically by the TanStack Router Vite plugin
  (`autoCodeSplitting: true` in `vite.config.ts`).

> Note: a dedicated row-virtualisation library (e.g. `react-window`) was **not** added because no new
> dependency could be installed in this offline environment; pagination keeps the DOM small in the
> interim and the table is structured so virtualisation can be dropped in later without changing the
> data layer.

## 16. Testing

Vitest + React Testing Library are listed as dev dependencies in `package.json`, but no test files were
added in this pass (no network access to install/verify the test runner in this environment). Suggested
first tests once you have `npm install` locally: `utils/scoring.test.ts`, `utils/conflictDetection.test.ts`,
and a smoke test that every route renders.

## 17. Running the Project

```bash
npm install
npm run dev       # start the dev server (also regenerates routeTree.gen.ts)
npm run build     # production build
npm run preview   # preview the production build
npm run lint       # if configured in package.json
```

> This build was assembled in a sandboxed environment with no network access, so `npm install` has not
> been run here and the build has not been executed/verified locally. Please run the commands above
> after unzipping to install dependencies, regenerate `routeTree.gen.ts`, and confirm the production
> build.

## 18. Environment Variables

None required. This is a frontend-only build with no backend dependency.

## 19. Backend Integration Readiness

Every "backend" behaviour is isolated behind a small number of seams so it can be swapped for real
REST/WebSocket calls without touching the UI:

- `src/data/*.ts` → replace generators with fetch calls (ideally behind TanStack Query, already wired
  in `__root.tsx`).
- `src/services/mock/aiService.ts` → replace `generateAIPlan` / `generateRescheduleOptions` with API
  calls to a real MDPS / RL rescheduler service; the return shapes (`BlockPlan[]`, `AIRecommendation[]`,
  `RescheduleOption[]`) are already the contract the UI consumes.
- `src/stores/*` → action bodies that currently mutate local state can instead call the service layer
  and update from the response; components never talk to `data/`/`services/` directly.
- Live train positions (`operationsStore.tick`) can be replaced by a WebSocket subscription that calls
  the same `set({ trains })`.

## 20. Synthetic Data Disclaimer

This frontend uses synthetic/demo data and simulated AI behaviour. It is not connected to live Indian
Railways operational systems. All "AI Simulation", "Synthetic Demo Data" and "Simulated Live Feed"
labels in the UI reflect this.

## 21. Known Gaps vs. the Original Brief (read this before a demo)

Being transparent about scope, since this was completed without network access to install dependencies
or run a build/typecheck:

- **MapLibre GL / Deck.gl were not installed.** The corridor visualisation is a custom SVG component
  instead (see §11) — visually distinct from a tile-based map, but functionally equivalent for this
  synthetic corridor and matches the brief's explicit fallback allowance.
- **No row virtualisation library.** Pagination is used instead (see §15).
- **The build has not been run.** `npm install`, `npm run dev` and `npm run build` all need to be run
  locally to install dependencies, regenerate `routeTree.gen.ts`, and catch any TypeScript issues —
  none of this could be executed in the sandboxed authoring environment.
- **Vitest/Playwright test files were not written** (see §16).
- Command/Division selectors on the Planner page and a couple of small controls are presentational only
  (single-corridor demo) rather than functionally filtering data.
