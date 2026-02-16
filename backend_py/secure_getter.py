# secure_getter.py

from cryptography.fernet import Fernet
from dotenv import load_dotenv
import numpy as np
import cv2
import os


# Load environment variables from .env file
load_dotenv()

SHARED_KEY = os.getenv('IMAGE_KEY')
cipher = Fernet(SHARED_KEY)


def decrypt_image(encrypted_image_path):
    if not os.path.exists(encrypted_image_path):
        print(f"[ERROR] Encrypted image file not found: {encrypted_image_path}")
        return None
    
    # Read the encrypted image data from the specified file path
    with open(encrypted_image_path, 'rb') as encrypted_file:
        encrypted_data = encrypted_file.read()
        print(f"\n[INFO] Read encrypted image data from: {encrypted_image_path} (size: {len(encrypted_data)} bytes)")
        print(f"[DEBUG] Encrypted image data (first 100 bytes): {encrypted_data[:100]}")

    try:
        # Decrypt the image
        decrypted_data = cipher.decrypt(encrypted_data)
        print(f"\n[INFO] Decrypted image data (size: {len(decrypted_data)} bytes)")

        # Convert in OpenCv image format
        nparr = np.frombuffer(decrypted_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        print(f"[INFO] Decrypted image successfully converted to OpenCV format")
        
        if img is not None:
            cv2.imshow("Decrypted Image", img)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
    
    except Exception as e:
        print(f"[ERROR] Failed to decrypt image: {e}")
        return None
    
# Example usage
if __name__ == "__main__":
    encrypted_image_path = "backend_py/encrypted/encrypted_image.bin"
    decrypt_image(encrypted_image_path)