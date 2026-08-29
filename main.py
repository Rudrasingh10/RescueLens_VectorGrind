from fastapi.responses import FileResponse
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from PIL import Image
from datetime import datetime, timezone
from geotagger import extract_gps
import io, hashlib, random

app = FastAPI(title="RescueLens API", version="1.0")

@app.get("/", include_in_schema=False)
def home():
    return FileResponse(Path(__file__).parent / "index.html")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_PATH = Path(__file__).parent / "models" / "RescueLens_best.pt"
MODEL = None
YOLO_MODE = False
MODEL_ERROR = None

try:
    from ultralytics import YOLO
    if MODEL_PATH.exists():
        MODEL = YOLO(str(MODEL_PATH))
        YOLO_MODE = True
    else:
        MODEL_ERROR = f"Model not found: {MODEL_PATH}"
except Exception as exc:
    MODEL_ERROR = f"YOLO load failed: {type(exc).__name__}: {exc}"
    MODEL = None

THREATS = [("Rising water",24),("Structural debris",18),("Fire / smoke",22),("Blocked access",14)]

def score_event(severity, confidence, accessibility, threat_weight):
    score = round(0.40*severity + 0.25*(confidence*100) + 0.20*threat_weight + 0.15*(100-accessibility))
    priority = "CRITICAL" if score >= 78 else "HIGH" if score >= 62 else "NORMAL"
    return score, priority

def demo_events(raw: bytes):
    seed=int(hashlib.sha256(raw or b"demo").hexdigest()[:12],16)
    rng=random.Random(seed); base_lat,base_lng=21.2510,81.6290; events=[]
    for i in range(rng.randint(4,6)):
        threat,tw=rng.choice(THREATS); conf=round(rng.uniform(.80,.97),2)
        sev=rng.randint(48,94); access=rng.randint(28,88); risk,priority=score_event(sev,conf,access,tw)
        events.append({"id":f"V-{i+1:02d}","label":"possible_survivor",
            "latitude":round(base_lat+rng.uniform(-.006,.006),6),
            "longitude":round(base_lng+rng.uniform(-.006,.006),6),
            "confidence":conf,"threat":threat,"severity":sev,"accessibility":access,
            "risk_score":risk,"priority":priority,"recommended_route":"Route A" if access>=55 else "Route B",
            "source":"DEMO_SIMULATION"})
    events.sort(key=lambda x:x["risk_score"],reverse=True)
    for rank,e in enumerate(events,1): e["rank"]=rank
    return events

def yolo_events(raw: bytes):
    if not MODEL:
        return None
    try:
        image = Image.open(io.BytesIO(raw)).convert("RGB")
        result = MODEL.predict(
            source=image,
            imgsz=512,
            conf=0.35,
            max_det=20,
            device="cpu",
            verbose=False,
        )[0]
    except Exception as exc:
        raise RuntimeError(f"YOLO inference failed: {type(exc).__name__}: {exc}") from exc

    names=result.names; events=[]
    if result.boxes is None: return []
    for i,box in enumerate(result.boxes):
        conf=float(box.conf[0])
        if conf < .35: continue
        cls=int(box.cls[0]); label=str(names.get(cls,cls))
        x1,y1,x2,y2=[float(v) for v in box.xyxy[0].tolist()]
        cx=(x1+x2)/2; cy=(y1+y2)/2
        lat=round(21.2510+(cy/max(image.height,1)-.5)*.012,6)
        lng=round(81.6290+(cx/max(image.width,1)-.5)*.012,6)
        person="person" in label.lower() or "human" in label.lower()
        severity=78 if person else 52; access=62; threat="Person detected" if person else label
        risk,priority=score_event(severity,conf,access,18 if person else 10)
        events.append({"id":f"D-{i+1:02d}","label":label,"latitude":lat,"longitude":lng,
            "confidence":round(conf,2),"threat":threat,"severity":severity,"accessibility":access,
            "risk_score":risk,"priority":priority,"recommended_route":"Route A",
            "source":"YOLO","bbox":[round(x1),round(y1),round(x2),round(y2)]})
    events.sort(key=lambda x:x["risk_score"],reverse=True)
    for rank,e in enumerate(events,1): e["rank"]=rank
    return events

@app.get("/api/health")
def health():
    return {
        "ok": True,
        "mode": "YOLO" if YOLO_MODE else "DEMO_SIMULATION",
        "model_loaded": YOLO_MODE,
        "model_path": str(MODEL_PATH),
        "model_error": MODEL_ERROR,
        "message": "Live YOLO model enabled." if YOLO_MODE else "Demo mode active."
    }

@app.post("/api/analyze")
async def analyze(file: UploadFile=File(...)):
    raw=await file.read()
    try:
        image=Image.open(io.BytesIO(raw)); size={"width":image.width,"height":image.height}
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Unsupported/corrupt image: {type(exc).__name__}: {exc}")

    real_gps = extract_gps(raw)

    inference_fallback = False
    try:
        events=yolo_events(raw) if YOLO_MODE else None
    except RuntimeError:
        # Keep the live demo usable when a particular image causes a model/runtime issue.
        # The fallback is deterministic for the uploaded image and is clearly labelled below.
        events=None
        inference_fallback=True

    mode="YOLO" if events is not None else "DEMO_SIMULATION"
    if events is None: events=demo_events(raw)

    if real_gps:
        lat, lng = real_gps
        for e in events:
            e["latitude"] = lat
            e["longitude"] = lng
            e["geotag_source"] = "IMAGE_EXIF_GPS"
    else:
        for e in events:
            e["geotag_source"] = "ESTIMATED"

    response_mode = "DEMO_SIMULATION_FALLBACK" if inference_fallback else mode
    return {"ok":True,"mode":response_mode,"filename":file.filename,"image_size":size,
        "analyzed_at":datetime.now(timezone.utc).isoformat(),
        "summary":{"detections":len(events),
            "critical":sum(e["priority"]=="CRITICAL" for e in events),
            "high":sum(e["priority"]=="HIGH" for e in events),
            "normal":sum(e["priority"]=="NORMAL" for e in events)},
        "events":events}