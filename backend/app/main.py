import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.routes.ocr_routes import router as ocr_router

app = FastAPI(title="MacaAksara API")

# Enable CORS for frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(ocr_router)

@app.on_event("startup")
def on_startup():
    from backend.app.models.database import init_db
    init_db()

# Mount frontend directory for static assets directly at the root /
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
frontend_path = os.path.join(backend_dir, "frontend")

if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")
else:
    print(f"[WARNING] Frontend directory '{frontend_path}' was not found. API server will run without static assets.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
