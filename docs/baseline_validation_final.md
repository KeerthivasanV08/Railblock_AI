# RailBlock AI — Baseline Validation (Final Release Audit)

**Date:** 2026-09-10  
**Branch:** `final-validation-2026-09-10`  
**Baseline Commit:** `b9a4a54bed483591bac108d99507d9b19f81b2f4`  
**Status:** VERIFIED BASELINE  

---

## Baseline Verification Matrix

| Claim / Metric | Expected Value | Source Code / Data File | Runtime Evidence / Output | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Canonical Corridor** | Chennai Egmore (MS) → Thoothukudi (TN) | `data/raw/network/stations.csv` | 648.228 km total chainage across 69 stations | **VERIFIED** |
| **Station Count** | 69 stations | `data/raw/network/stations.csv` | `len(pd.read_csv('stations.csv')) == 69` | **VERIFIED** |
| **Planning Sections** | 68 RailBlock Planning Sections | `data/raw/network/block_sections.csv` | `SEC_001` to `SEC_068` (Project-derived planning sections) | **VERIFIED** |
| **Divisions Covered** | MAS (Chennai), TPJ (Tiruchchirappalli), MDU (Madurai) | `data/raw/network/stations.csv` | Division column mapping across MAS, TPJ, MDU | **VERIFIED** |
| **Timetable Size** | 50,000 synthetic schedule rows | `data/raw/traffic/train_timetable.csv` | `len(df) == 50000` (500 unique trains over 7 days) | **VERIFIED** |
| **Timetable Section Coverage** | 68 / 68 planning sections | `data/raw/traffic/train_timetable.csv` | Unique section IDs present: `SEC_001`–`SEC_068` | **VERIFIED** |
| **Backend Test Suite** | 131 / 131 tests passing | `backend/tests` | `131 passed, 37 warnings in 97s` (`pytest`) | **VERIFIED** |
| **Frontend Build** | Vite Nitro Production Build | `frontend/` | `npm run build` completed in 4.00s (`.output/public`) | **VERIFIED** |
| **TypeScript Strict** | Zero compilation errors | `frontend/tsconfig.json` | `npx tsc --noEmit` passed with 0 errors | **VERIFIED** |
| **Backend Runtime** | FastAPI Server on port 8765 | `backend/app/main.py` | Operational on `http://127.0.0.1:8765` | **VERIFIED** |
| **Enterprise RBAC** | Centralized COA Decision Support | `backend/app/api/auth/` | Centralized COA authority dashboard | **OUT OF SCOPE** |
