# RescueLens — Full-Stack SIH MVP

## What is included

- `index.html` — complete RescueLens command-center frontend.
- `backend/main.py` — FastAPI API.
- Optional real Ultralytics YOLO inference when `backend/models/best.pt` is present.
- Demo simulation fallback when no model is loaded.
- `render.yaml` — Render Web Service deployment config.

## Production/demo architecture

Vercel:
- Hosts the public frontend: `https://rescuelens.vercel.app`

Render:
- Hosts the FastAPI backend at a public `onrender.com` URL.
- Free plan is suitable for testing/demo, with spin-down after inactivity.

## Backend deploy

On Render:
1. New → Web Service.
2. Connect this GitHub repository.
3. Root directory: `backend`.
4. Build: `pip install -r requirements.txt`
5. Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Plan: Free.
7. Deploy.

## Connect the frontend

After Render gives the API URL, edit the `API` line in `index.html` to the public API URL, e.g.

`const API = "https://rescuelens-api.onrender.com";`

Commit the change to GitHub. Vercel will redeploy automatically.

## Real YOLO

Put the trained model on the backend host as:

`backend/models/best.pt`

Do not put private/sensitive model weights in the public GitHub repository.

## Important MVP boundary

Without a trained disaster-specific model and real UAV GPS/telemetry/georeferencing, the backend's fallback mode is explicitly `DEMO_SIMULATION`. Do not present simulated coordinates/detections as real field measurements.
