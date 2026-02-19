# main.py

from fastapi import FastAPI

from backend_py.models import EnrollRequest
from backend_py.secure_getter import decrypt_image_from_string
from backend_py.face_engine import FaceEngine

app = FastAPI()

@app.get("/")
def read_root():
    return {
    "app_name": "AeroID",
    "message": "Welcome to the Face Recognition API!",
    "status": "System Online & Secure",
    "endpoints": {
        "docs": "/docs",
        "enroll": "/api/enroll",
        "verify": "/api/verify"
    }
}


# Enroll endpoint
@app.post("/api/enroll")
async def enroll(request: EnrollRequest):
    
    print(f"[INFO] Received encrypted image data: {request.encrypted_image}")

    decrypted_image = decrypt_image_from_string(request.encrypted_image)

    print(f"[INFO] Getting the biometric vector from the decrypted image")

    fe = FaceEngine()
    biometric_vector = fe.generate_vector(decrypted_image)

    return {"message": "Received data successfully",
            "biometric_vector": biometric_vector}
    


@app.get("/api/verify")
def verify():
    return {"message": "Verification endpoint - To be implemented"}