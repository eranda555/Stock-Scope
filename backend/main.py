"""Stock Scope - FastAPI Backend

Reuses existing Python modules from the project root via sys.path import.
The original Streamlit app remains untouched and fully functional.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow imports from the project root (where the original .py files live)
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import cse, stocks, analysis

app = FastAPI(
    title="Stock Scope API",
    description="REST API for stock market analysis (CSE, US markets)",
    version="1.0.0",
)

# CORS – allow the React dev server on localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(cse.router, prefix="/api/cse", tags=["CSE"])
app.include_router(stocks.router, prefix="/api/stocks", tags=["Stocks"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])


@app.get("/api/health", tags=["Health"])
async def health_check():
    """Simple health-check endpoint."""
    return {"status": "ok", "app": "Stock Scope API", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
