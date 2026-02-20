# main.py

from fastapi import FastAPI

from app.models import EnrollRequest, VerifyRequest
from app.security.secure_getter import decrypt_image_from_string
from app.face_engine import FaceEngine

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

    try:
    
        print(f"[INFO] Received encrypted image data: {request.encrypted_image}")

        decrypted_image = decrypt_image_from_string(request.encrypted_image)

        print(f"[INFO] Getting the biometric vector from the decrypted image")

        fe = FaceEngine()
        biometric_vector = fe.generate_vector(decrypted_image)

        return {"message": "Received data successfully",
                "biometric_vector": biometric_vector}
    except Exception as e:
        print(f"[ERROR] An error occurred during enrollment: {e}")

        return {"message": f"An error occurred during enrollment: {str(e)}",
                "biometric_vector": None}
    


@app.post("/api/verify")
def verify(request: VerifyRequest):
    
    try:
        print(f"[INFO] Received data successfully for verification")

        decrypted_image = decrypt_image_from_string(request.encrypted_image)
        print(f"[INFO] Getting the biometric vector from the decrypted image for verification")
        fe = FaceEngine()
        results_image_to_verify = fe.generate_vector(decrypted_image)

        biometric_vector_to_verify = results_image_to_verify["biometric_vector"]

        #print(biometric_vector_to_verify)

        results = fe.compare_vectors(biometric_vector_to_verify, request.biometric_vector)

        return {"message": "Received data successfully",
                "verification_results": results}
    except Exception as e:
        print(f"[ERROR] An error occurred during verification: {e}")

        return {"message": f"An error occurred during verification: {str(e)}",
                "verification_results": None}


