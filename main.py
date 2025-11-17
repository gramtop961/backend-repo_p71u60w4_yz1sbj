import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from database import db, create_document, get_documents
from schemas import Track

app = FastAPI(title="Music App API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Music App Backend Running"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"

            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response

# API models
class TrackCreate(BaseModel):
    title: str
    artist: str
    audio_url: str
    cover_url: Optional[str] = None
    duration: Optional[float] = None


@app.get("/api/tracks", response_model=List[Track])
def list_tracks(limit: int = 50):
    """Return a list of tracks from the database"""
    try:
        docs = get_documents("track", {}, limit)
        # Convert MongoDB documents to Track models
        tracks: List[Track] = []
        for d in docs:
            d_id = str(d.get("_id")) if d.get("_id") else None
            # Remove Mongo's _id for Pydantic model compatibility
            d.pop("_id", None)
            tracks.append(Track(**d))
        return tracks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tracks", response_model=Track)
def create_track(payload: TrackCreate):
    """Create a new track entry in the database"""
    try:
        track = Track(
            title=payload.title,
            artist=payload.artist,
            audio_url=payload.audio_url,
            cover_url=payload.cover_url,
            duration=payload.duration,
            likes=0,
            play_count=0,
        )
        _id = create_document("track", track)
        return track
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
