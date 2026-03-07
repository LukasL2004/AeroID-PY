# test_compare.py
# Manual comparison of two images that SIMULATES EXACTLY what the API does.
# Uses `secure_sender` (client side), `secure_getter` (server side), 
# and `vector_codec` to compress/decompress.
#
# Usage:
#   1. Set IMG_1 and IMG_2 below to the paths of the images you want to compare.
#   2. Run:  py tests/test_compare.py

import sys
import os
from pathlib import Path
from datetime import datetime

# Add the project root to PATH for local imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.face_engine import FaceEngine
from app.vector_codec import compress_vector, decompress_vector
from app.security.secure_sender import cipher
from app.security.secure_getter import decrypt_image_from_string

# ──────────────────────────────────────────────────────────────
#  SET YOUR IMAGE PATHS HERE
# ──────────────────────────────────────────────────────────────
IMG_1 = "assets/imgs/Lukas_2.jpeg"
IMG_2 = "assets/imgs/Lukas_6.jpeg"
# ──────────────────────────────────────────────────────────────

def resolve(path: str) -> str:
    """Convert a relative path to absolute based on the project root."""
    p = Path(path)
    if not p.is_absolute():
        p = Path(__file__).parent.parent / p
    return str(p)

def encrypt_image_for_api(image_path: str) -> str:
    """Simulates frontend reading the image and encrypting it."""
    with open(image_path, "rb") as f:
        raw_data = f.read()
    # The API expects a string, so we decode the bytes outputted by Fernet
    encrypted = cipher.encrypt(raw_data)
    return encrypted.decode("utf-8")

def simulate_api_enroll(engine: FaceEngine, encrypted_image_string: str):
    """Simulates the POST /api/enroll logic."""
    print(f"      [Enroll] Decrypting image from string...")
    # 1. Decrypt Image into OpenCV format
    decrypted_cv2_image = decrypt_image_from_string(encrypted_image_string)
    
    if decrypted_cv2_image is None:
        return {"status": "error", "message": "Failed to decrypt or decode image"}

    print(f"      [Enroll] Generating biometric vector...")
    # 2. Generate Vector
    res = engine.generate_vector(decrypted_cv2_image)
    if res["status"] != "success":
        return res

    raw_vector = res["biometric_vector"]

    print(f"      [Enroll] Compressing vector...")
    # 3. Compress Vector
    compressed_vec = compress_vector(raw_vector)

    return {
        "status": "success",
        "raw_vector": raw_vector,
        "compressed_vector": compressed_vec,
    }

def simulate_api_verify(engine: FaceEngine, encrypted_image_string: str, compressed_vector_to_compare: str):
    """Simulates the POST /api/verify logic."""
    print(f"      [Verify] Decrypting image from string...")
    # 1. Decrypt image
    decrypted_cv2_image = decrypt_image_from_string(encrypted_image_string)
    
    if decrypted_cv2_image is None:
        return {"status": "error", "message": "Failed to decrypt or decode image"}

    print(f"      [Verify] Generating vector from live image...")
    # 2. Generate vector from "live" image
    res = engine.generate_vector(decrypted_cv2_image)
    if res["status"] != "success":
        return res
    
    live_vector = res["biometric_vector"]

    print(f"      [Verify] Compressing live vector...")
    # 3. Compress the live vector (for logging purposes)
    live_compressed_vec = compress_vector(live_vector)

    print(f"      [Verify] Decompressing the QR vector...")
    # 4. Decompress the received vector (from QR/DB)
    qr_vector = decompress_vector(compressed_vector_to_compare)

    print(f"      [Verify] Comparing vectors...")
    # 5. Compare
    comparison_results = engine.compare_vectors(live_vector, qr_vector)
    
    # Pack intermediate data for the log
    comparison_results["intermediates"] = {
        "live_raw_vector": live_vector,
        "live_compressed_vector": live_compressed_vec,
        "qr_decompressed_vector": qr_vector
    }
    
    return comparison_results

def save_results(engine, label_1, img_1_encrypted, enroll_res, label_2, img_2_encrypted, verify_res):
    """Save all data to a text file in tests/model_tests/."""
    output_dir = Path(__file__).parent / "model_tests"
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name_1 = Path(label_1).stem
    name_2 = Path(label_2).stem
    filename = f"API_SIM_{name_1}_vs_{name_2}_{timestamp}.txt"
    filepath = output_dir / filename

    sep = "=" * 65

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"{sep}\n")
        f.write(f"  API END-TO-END SIMULATION: {name_1} vs {name_2}\n")
        f.write(f"  Model:    {engine.model_name}\n")
        f.write(f"  Detector: {engine.detector}\n")
        f.write(f"  Date:     {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"{sep}\n\n")

        # --- IMAGE 1 (Enrollment) ---
        f.write(f"{'─' * 65}\n  IMAGE 1 (Simulated ENROLL): {name_1}\n{'─' * 65}\n\n")
        f.write(f"  [ENCRYPTED IMAGE PAYLOAD]\n{img_1_encrypted}\n\n")
        if enroll_res["status"] == "success":
            f.write(f"  [SERVER - RAW VECTOR GENERATED] ({len(enroll_res['raw_vector'])} dims)\n{enroll_res['raw_vector']}\n\n")
            f.write(f"  [SERVER - COMPRESSED VECTOR (Sent to client via QR)]\n{enroll_res['compressed_vector']}\n\n")
        else:
            f.write(f"  [SERVER ERROR] {enroll_res.get('message')}\n\n")

        # --- IMAGE 2 (Verification) ---
        f.write(f"{'─' * 65}\n  IMAGE 2 (Simulated VERIFY): {name_2}\n{'─' * 65}\n\n")
        f.write(f"  [ENCRYPTED IMAGE PAYLOAD]\n{img_2_encrypted}\n\n")
        
        if "is_match" in verify_res:
            live_vector = verify_res["intermediates"]["live_raw_vector"]
            live_compressed = verify_res["intermediates"]["live_compressed_vector"]
            f.write(f"  [SERVER - RAW VECTOR GENERATED] ({len(live_vector)} dims)\n{live_vector}\n\n")
            f.write(f"  [SERVER - COMPRESSED VECTOR]\n{live_compressed}\n\n")
            f.write(f"{sep}\n  VERIFICATION RESULT\n{'─' * 65}\n")
            f.write(f"  Match    : {'YES' if verify_res['is_match'] else 'NO'}\n")
            f.write(f"  Distance : {verify_res['distance']:.6f}\n")
            f.write(f"  Threshold: {engine.threshold}\n")
            f.write(f"{sep}\n")
        else:
            f.write(f"  [SERVER ERROR] Verification failed: {verify_res.get('message', 'Unknown Error')}\n\n")

    print(f"\n[SAVED] {filepath}")

def main():
    engine = FaceEngine()

    print("=" * 65)
    print(f"  API END-TO-END SIMULATION")
    print(f"  Model:    {engine.model_name}")
    print(f"  Detector: {engine.detector}")
    print("=" * 65)

    path_1 = resolve(IMG_1)
    path_2 = resolve(IMG_2)

    # 1. Client reads and encrypts Image 1
    print(f"\n[CLIENT] Encrypting Image 1: {Path(path_1).name}")
    enc_img_1 = encrypt_image_for_api(path_1)
    
    # 2. Simulate API Enroll (Image 1)
    print(f"[SERVER] Processing Enroll request for Image 1...")
    enroll_res = simulate_api_enroll(engine, enc_img_1)
    if enroll_res["status"] != "success":
        print(f"      ✗ Enroll Failed: {enroll_res.get('message')}")
        save_results(engine, path_1, enc_img_1, enroll_res, path_2, "N/A", {"status": "error", "message": "Enroll failed"})
        return
        
    print(f"      ✓ Vector compressed successfully!")
    qr_vector = enroll_res["compressed_vector"]

    # 3. Client reads and encrypts Image 2
    print(f"\n[CLIENT] Encrypting Image 2: {Path(path_2).name}")
    enc_img_2 = encrypt_image_for_api(path_2)

    # 4. Simulate API Verify (Image 2 + qr_vector)
    print(f"[SERVER] Processing Verify request for Image 2...")
    verify_res = simulate_api_verify(engine, enc_img_2, qr_vector)
    
    if "is_match" not in verify_res:
        print(f"      ✗ Verify Failed: {verify_res.get('message')}")
    else:
        print(f"      ✓ Verification complete!")
        print("\n" + "=" * 65)
        print(f"  VERIFICATION RESULT")
        print("-" * 65)
        print(f"  Match    : {'✓ YES' if verify_res['is_match'] else '✗ NO'}")
        print(f"  Distance : {verify_res['distance']:.6f}")
        print(f"  Threshold: {engine.threshold}")
        print("=" * 65)

    # Save to file
    save_results(engine, path_1, enc_img_1, enroll_res, path_2, enc_img_2, verify_res)


if __name__ == "__main__":
    main()
