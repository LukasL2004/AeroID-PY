# testing.py

from face_engine import FaceEngine


def test_face_engine(img_path):
    face_engine = FaceEngine()

    results = face_engine.generate_vector(img_path)

    print("\n[TEST] Face Engine Test Results:")
    print(f"Status: {results['status']}")

    return results['biometric_vector'] if results['status'] == 'success' else None


def test_compare_vectors(live_vector, qr_vector):
    fe = FaceEngine()

    results = fe.compare_vectors(live_vector, qr_vector)

    print("\n[TEST] Compare Vectors Test Results:")
    print(f"Match: {results['is_match']}")
    print(f"Distance: {results['distance']}")



if __name__ == "__main__":
    qr_vector = test_face_engine("backend_py/imgs/Eu.jpg")
    live_vector = test_face_engine("backend_py/imgs/webcam.jpg")

    test_compare_vectors(live_vector, qr_vector)
