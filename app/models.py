# models.py

from pydantic import BaseModel

class EnrollRequest(BaseModel):
    encrypted_image: str # Encrypted image data


class VerifyRequest(BaseModel):
    encrypted_image: str # Encrypted image data
    biometric_vector: str # Biometric vector to compare against