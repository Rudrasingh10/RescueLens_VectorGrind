# RescueLens — Full-Stack SIH MVP

## What is included

- `index.html` — RescueLens command-center frontend.
- `main.py` — FastAPI API with live Ultralytics YOLO inference.
- `models/RescueLens_best.pt` — trained RescueLens YOLO model.
- `geotagger.py` — EXIF GPS extraction.
- `render.yaml` — Render Web Service deployment config.

## Production/demo architecture

**Vercel**
- Public frontend: `https://rescuelens.vercel.app`

**Render**
- Public FastAPI backend.
- The frontend is configured to call `https://rescuelens-api.onrender.com` after the backend is deployed.

## Deploy the backend

Render's FastAPI deployment uses a Python Web Service with:

- Build: `pip install -r requirements.txt`
- Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Health check: `/api/health`

You can create the service from the `render.yaml` Blueprint or from **New → Web Service** in Render, connect this GitHub repository, and deploy from `main`.

## One-click Render deployment

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Rudrasingh10/RescueLens_VectorGrind)

## Connect the frontend

The frontend uses:

`const API = "https://rescuelens-api.onrender.com";`

After the Render service is live at that hostname, Vercel can serve the existing frontend directly.

## Important MVP boundary

The live YOLO path is used when the trained model loads successfully. If the model cannot be loaded, the backend falls back to an explicitly labelled demo simulation. Real GPS is only taken from image EXIF when available; otherwise coordinates are estimated.
