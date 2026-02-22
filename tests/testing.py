# testing.py

import sys
from pathlib import Path



# Add parent directory to path so we can import app module
sys.path.insert(0, str(Path(__file__).parent.parent))


from app.vector_codec import compress_vector
from app.face_engine import FaceEngine

def test_face_engine(img_path):
    # Convert relative path to absolute if needed
    if not Path(img_path).is_absolute():
        project_root = Path(__file__).parent.parent
        img_path = str(project_root / img_path)
    
    face_engine = FaceEngine()

    results = face_engine.generate_vector(img_path)

    print("\n[TEST] Face Engine Test Results:")
    print(f"Status: {results['status']}")

    size_of_vector = sys.getsizeof(results['biometric_vector']) if results['status'] == 'success' else 0
    print(f"\n [Test] Size of biometric vector: {size_of_vector} bytes")


    with open("test_biometric_vector.txt", "w") as f:
        f.write(str(compress_vector(results["biometric_vector"])))

    return results['biometric_vector'] if results['status'] == 'success' else None


def test_compare_vectors(live_vector, qr_vector):
    fe = FaceEngine()

    results = fe.compare_vectors(live_vector, qr_vector)

    print("\n[TEST] Compare Vectors Test Results:")
    print(f"Match: {results['is_match']}")
    print(f"Distance: {results['distance']}")
    



if __name__ == "__main__":
    qr_vector = test_face_engine("assets/imgs/Eu.jpg")
    live_vector = test_face_engine("assets/imgs/Zbuce_2.jpeg")

    #test_compare_vectors(live_vector, qr_vector)
    test_face_engine("assets/imgs/Eu.jpg")
