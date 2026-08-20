# Eeknova AI Trainer

This repository contains:

- `yoga_project/` — FastAPI backend. Serves **all three modules** (Yoga, Chess, Zumba) from one server, plus auth, dashboard stats, and WebSocket pose/dance analysis.
- `frontend/` — Next.js frontend (Yoga, Chess, Zumba, dashboard, auth, settings).
- `Zumba/` — Zumba reference data and choreography source assets, read by the backend at runtime (path is relative to `yoga_project/`, so it does not need its own server).
- `scripts/` — one-off data build scripts (currently: the Zumba choreography → JSON converter).

There is **one backend process** and **one frontend process**. `chess_learning_system/` is a separate/legacy folder and is **not** used by the running app — the backend's chess logic lives in `yoga_project/chess_api.py` and `yoga_project/chess_engine.py`.

## Prerequisites

- Python 3.10+
- Node.js 18+

## Backend (FastAPI)

**The backend must be started from inside `yoga_project/`.** It opens its database (`yoga_users.db`) and a few other files using paths relative to the current working directory, so running `python main.py` from anywhere else (e.g. the repo root) will create a second, empty database and the app will look broken — sessions, streaks, and login state will not match what the frontend expects. This is the single most common setup mistake.

1. Create and activate a virtual environment (from the repo root):

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r yoga_project/requirements.txt
```

This pulls in `torch` and `ultralytics` (YOLO pose detection), so the first install can take a while.

3. Confirm the pose models are present (they are checked into `yoga_project/` and should already be there after cloning):

```text
yoga_project/yolo11x-pose.pt   (Yoga)
yoga_project/yolo11n-pose.pt   (Zumba — lighter/faster model for real-time dance analysis)
```

4. Start the server **from `yoga_project/`**:

```bash
cd yoga_project
python main.py
```

The database tables are created automatically on first run — no separate migration step.

Backend will be available at:

- REST: `http://localhost:8002`
- WebSocket: `ws://localhost:8002`

## Frontend (Next.js)

1. Install dependencies:

```bash
cd frontend
npm install
```

2. Create `frontend/.env.local`:

```env
OPENAI_API_KEY=your-openai-api-key
NEXT_PUBLIC_OPENAI_API_KEY=your-openai-api-key
```

Only needed if the backend is **not** running on `localhost:8002` (e.g. a different machine or port):

```env
NEXT_PUBLIC_YOGA_API_URL=http://localhost:8002
NEXT_PUBLIC_YOGA_WS_URL=ws://localhost:8002
```

3. Start the dev server:

```bash
npm run dev
```

(`npm run dev:turbo` uses Turbopack instead of webpack, if you want faster rebuilds.)

Frontend will be available at:

- `http://localhost:3000`

## Running both together

Two terminals, in this order:

```bash
# Terminal 1 — backend
cd yoga_project
python main.py

# Terminal 2 — frontend
cd frontend
npm run dev
```

Then open `http://localhost:3000`.

## Zumba choreography data

The Zumba timeline JSON the frontend reads (`frontend/public/zumba-mappings-18steps.json`) is generated from an Excel workbook, not hand-edited. If the choreography workbook changes, regenerate it from the repo root:

```bash
python scripts/build_zumba_mapping_json.py
```

The script validates the workbook against the actual GLB animation files and fails loudly (with the specific mismatch) if something doesn't line up, so a clean run is a reliable sign the data is correct.

## Troubleshooting

- **Zumba avatar has no sound / seems out of date on the Holobox or another machine**: almost always the backend was started from the wrong folder. Kill it and restart with `cd yoga_project && python main.py` — see the warning above.
- **WebSocket keeps disconnecting during a Zumba session**: usually pose-detection inference falling behind the camera feed on slower hardware. The Zumba processor already uses the lighter `yolo11n-pose.pt` model for this reason; if it still happens, check the backend terminal for repeated processing-timeout errors.
- **Frontend can't reach the backend**: confirm the backend is actually running on port 8002 (`http://localhost:8002` should respond), and that `frontend/.env.local` isn't pointing at a stale URL.
