# testing.py

from app.face_engine import FaceEngine
import sys


def test_face_engine(img_path):
    face_engine = FaceEngine()

    results = face_engine.generate_vector(img_path)

    print("\n[TEST] Face Engine Test Results:")
    print(f"Status: {results['status']}")

    size_of_vector = sys.getsizeof(results['biometric_vector']) if results['status'] == 'success' else 0
    print(f"\n [Test] Size of biometric vector: {size_of_vector} bytes")

    with open("test_biometric_vector.txt", "w") as f:
        f.write(str(results["biometric_vector"]))

    return results['biometric_vector'] if results['status'] == 'success' else None


def test_compare_vectors(live_vector, qr_vector):
    fe = FaceEngine()

    results = fe.compare_vectors(live_vector, qr_vector)

    print("\n[TEST] Compare Vectors Test Results:")
    print(f"Match: {results['is_match']}")
    print(f"Distance: {results['distance']}")
    



if __name__ == "__main__":
    qr_vector = test_face_engine("backend_py/imgs/Eu.jpg")
    live_vector = test_face_engine("backend_py/imgs/Zbuce_2.jpeg")

    #test_compare_vectors(live_vector, qr_vector)
    test_face_engine("backend_py/imgs/Zbuce_1.jpeg")
