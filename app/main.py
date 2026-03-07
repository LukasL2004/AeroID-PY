# main.py

from fastapi import FastAPI

from app.models import EnrollRequest, VerifyRequest
from app.security.secure_getter import decrypt_image_from_string
from app.face_engine import FaceEngine
from app.yolo_filter import YOLOFilter
from app.vector_codec import compress_vector, decompress_vector

app = FastAPI()

# ── Global instances (loaded once at startup) ──────────────────────────
yolo = YOLOFilter()        # Treapta 1 – The Bouncer
fe   = FaceEngine()        # Treapta 2 – The Detective


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
def enroll(request: EnrollRequest):

    try:
    
        print(f"[INFO] Received encrypted image data: {request.encrypted_image}")

        decrypted_image = decrypt_image_from_string(request.encrypted_image)

        # ── Treapta 1: YOLO scan ──────────────────────────────────────
        scan = yolo.scan_frame(decrypted_image)
        if not scan["ok"]:
            return {
                "message": scan["message"],
                "biometric_vector": None,
                "multiple_persons": scan["persons_found"] > 1
            }

        # ── Treapta 2: DeepFace embedding ─────────────────────────────
        print(f"[INFO] Getting the biometric vector from the decrypted image")

        biometric_vector = fe.generate_vector(decrypted_image)

        if biometric_vector.get("status") == "success":
            biometric_vector.update({
                "biometric_vector": compress_vector(biometric_vector["biometric_vector"])
            })

        return {"message": "Received data successfully",
                "biometric_vector": biometric_vector,
                "multiple_persons": False}
    
    except Exception as e:
        print(f"[ERROR] An error occurred during enrollment: {e}")

        return {"message": f"An error occurred during enrollment: {str(e)}",
                "biometric_vector": None}
    


@app.post("/api/verify")
def verify(request: VerifyRequest):
    
    try:
        print(f"[INFO] Received data successfully for verification")

        decrypted_image = decrypt_image_from_string(request.encrypted_image)

        # ── Treapta 1: YOLO scan ──────────────────────────────────────
        scan = yolo.scan_frame(decrypted_image)
        if not scan["ok"]:
            return {
                "message": scan["message"],
                "verification_results": None,
                "multiple_persons": scan["persons_found"] > 1
            }

        # ── Treapta 2: DeepFace embedding ─────────────────────────────
        print(f"[INFO] Getting the biometric vector from the decrypted image for verification")

        results_image_to_verify = fe.generate_vector(decrypted_image)

        if results_image_to_verify.get("status") == "error":
            return {
                "message": "Face recognition failed",
                "verification_results": results_image_to_verify,
                "multiple_persons": False
            }

        # Extract the biometric vector from the results to verify
        biometric_vector_to_verify = results_image_to_verify["biometric_vector"]

        # Decompress the biometric vectors
        qr_vector = decompress_vector(request.biometric_vector)

        # Compare the biometric vector from the image to verify with the biometric vector from the QR code
        results = fe.compare_vectors(biometric_vector_to_verify, qr_vector)

        return {"message": "Received data successfully",
                "verification_results": results,
                "multiple_persons": False}
    
    except Exception as e:
        print(f"[ERROR] An error occurred during verification: {e}")

        return {"message": f"An error occurred during verification: {str(e)}",
                "verification_results": None}


