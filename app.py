import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from database.storage import get_top_5_results
from main import run_pipeline

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Procurement Opportunities")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

executor = ThreadPoolExecutor(max_workers=2)

# Mount static folder
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def index():
    """Serve the simple interface."""
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse(index_file)


@app.get("/api/results/top5")
async def fetch_top_5():
    """Fetch the top 5 results saved in the database."""
    try:
        results = get_top_5_results()
        return JSONResponse({
            "status": "success",
            "count": len(results),
            "results": results
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e), "results": []}
        )


@app.post("/api/run-pipeline")
async def trigger_pipeline():
    """Execute main.py pipeline, save results in database, and return fresh top 5."""
    try:
        loop = asyncio.get_event_loop()
        top_results = await loop.run_in_executor(executor, run_pipeline)
        return JSONResponse({
            "status": "success",
            "message": "Pipeline completed",
            "count": len(top_results),
            "results": top_results
        })
    except Exception as e:
        print(f"Pipeline error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Pipeline failed: {str(e)}",
                "results": get_top_5_results()
            }
        )


if __name__ == "__main__":
    print("Server running on http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)
