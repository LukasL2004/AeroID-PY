# secure_sender.py

from cryptography.fernet import Fernet
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

#key = Fernet.generate_key()
#print(f"Key: {key.decode()}")

SHARED_KEY = os.getenv('IMAGE_KEY')
cipher = Fernet(SHARED_KEY)

def encrypt_image(image_path):

    if not os.path.exists(image_path):
        print(f"[ERROR] Image file not found: {image_path}")
        return None
    
    # Read the image data from the specified file path
    with open(image_path, 'rb') as image_file:
        raw_data = image_file.read()
        print(f"\n[INFO] Read image data from: {image_path} (size: {len(raw_data)} bytes)")
        print(f"[DEBUG] Original image data (first 100 bytes): {raw_data[:100]}")


    # Encrypt the image data using the shared key and Fernet cipher
    encrypt_data = cipher.encrypt(raw_data)
    print(f"\n[INFO] Encrypted image data (size: {len(encrypt_data)} bytes)")
    print(f"[DEBUG] Encrypted image data (first 100 bytes): {encrypt_data[:100]}")


    # Save the encrypted data to a new file
    # Ensure the encrypted directory exists
    encrypted_dir = 'backend_py/encrypted'
    os.makedirs(encrypted_dir, exist_ok=True)
    
    with open(os.path.join(encrypted_dir, 'encrypted_image.bin'), 'wb') as encrypted_file:
        encrypted_file.write(encrypt_data)
        print(f"\n[INFO] Encrypted image data saved to: {os.path.join(encrypted_dir, 'encrypted_image.bin')}")



# Example usage
if __name__ == "__main__":
    image_path = "backend_py/imgs/Zbuce_1.jpeg"
    encrypt_image(image_path)