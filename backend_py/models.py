# models.py

from pydantic import BaseModel

class EnrollRequest(BaseModel):
    encrypted_image: str # Encrypted image data