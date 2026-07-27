from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from backend.app.controllers.ocr_controller import perform_ocr_inference

router = APIRouter()

@router.post("/predict")
async def predict_javanese_script(
    file: UploadFile = File(...),
    is_webcam: bool = Form(False)
):
    try:
        # Read file bytes
        image_bytes = await file.read()
        
        # Save to debug file for diagnostic analysis
        try:
            with open("D:/MacaAksara/debug_input.png", "wb") as debug_f:
                debug_f.write(image_bytes)
        except Exception as err:
            print(f"[DEBUG] Failed to write debug input: {err}")
        
        # Invoke controller to run segment & inference
        result = perform_ocr_inference(image_bytes, is_webcam=is_webcam)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process prediction: {str(e)}")

@router.get("/training/status")
def get_training_status():
    import json
    import os
    # Path to backend/training_progress.json
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    progress_file = os.path.join(backend_dir, "training_progress.json")
    if not os.path.exists(progress_file):
        return {"status": "idle", "epoch": 0, "total_epochs": 0, "best_acc": 0.0}
    try:
        with open(progress_file, "r") as f:
            data = json.load(f)
        return data
    except Exception as e:
        return {"status": "error", "message": str(e)}
