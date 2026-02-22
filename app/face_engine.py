# face_engine.py

from deepface import DeepFace
import numpy as np
import cv2

from app.vector_codec import compress_vector, decompress_vector, transform_vector_to_f16



class FaceEngine:
    def __init__(self, model_name="ArcFace", detector="retinaface", threshold=0.5):
        self.model_name = model_name
        self.detector = detector
        self.threshold = threshold


    # Generate a biometric vector (embedding) from the input image using DeepFace
    def generate_vector(self, img_cv2):
        try:
            results = DeepFace.represent(
                img_path = img_cv2, # Pass the OpenCV image directly to DeepFace
                model_name = self.model_name,
                detector_backend = self.detector,
                enforce_detection = True, # True to ensure that a face is detected
            )

            biometric_vector = results[0]["embedding"] # Extract the embedding vector from the results


            print(f"[INFO] Biometric vector generated successfully: {biometric_vector[0:10]}")

            return {
                "status": "success",
                "biometric_vector": biometric_vector,
                "message": None
            }
        
        except ValueError:
            print("[ERROR] No face detected in the image. Please provide a valid image with a clear face.")
            return {
                "status": "error",
                "message": "No face detected in the image."
            }
        except Exception as e:
            print(f"[ERROR] An error occurred while generating the biometric vector: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
        
    
    def compare_vectors(self, live_vector, qr_vector):

        try:
            # Calculate the cosine distance between the two vectors
            a = np.array(qr_vector) # Convert the QR vector to a NumPy array
            b = np.array(live_vector) # Convert the live vector to a NumPy array

            # Compute the cosine similarity
            # Formula: cosine_similarity = 1 - (A . B) / (||A|| * ||B||)
            dot_product = np.dot(a, b) # Calculate the dot product of the two vectors
            norm_a = np.linalg.norm(a) # Calculate the magnitude (norm) of vector A
            norm_b = np.linalg.norm(b) # Calculate the magnitude (norm) of vector B

            # Calculate the cosine distance
            distance = 1 - (dot_product / (norm_a * norm_b)) 

            # Determine if the distance is within the threshold for a match
            if distance < self.threshold:
                is_match = True
                print(f"[INFO] Vectors match with distance: {distance}")

            else:
                is_match = False
                print(f"[INFO] Vectors do NOT match with distance: {distance}")

            return {
                "is_match": bool(is_match),
                "distance": float(distance),
                "message": None
            }
        
        except ValueError:
            print(f"[ERROR] Invalid vector")
            return {
                "is_match": False,
                "distance": None,
                "message": "Invalid vector"
            }
        
        except Exception as e:
            print(f"[ERROR] An error occurred while comparing vectors: {e}")
            return {
                "is_match": False,
                "distance": None,
                "message": str(e)
            }
        

    def resize_image(self, img_cv2, target_size=(600, 600)):
        try:
            resized_img = cv2.resize(img_cv2, target_size)
            print(f"[INFO] Image resized successfully to {target_size}")

            return resized_img

        except Exception as e:
            print(f"[ERROR] An error occurred while resizing the image: {e}")
            return img_cv2 # Return the original image if resizing fails