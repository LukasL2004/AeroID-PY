import os
import cv2
from deepface import DeepFace


def start_secure_gate():
    """
    Initialize and run a biometric authentication system using facial recognition.
    Captures video from the default camera and verifies faces against a reference image.
    """
    img_path = "backend_py/imgs/webcam.jpg"
    
    # Validate that the reference image exists before starting the system
    if not os.path.exists(img_path):
        print(f"ERROR: Reference image not found at: {img_path}")
        return

    # Initialize video capture from the default camera device
    cap = cv2.VideoCapture(1)

    print("Starting Secure Gate System...")
    
    counter = 0
    
    # Initialize UI state variables
    status_message = "Searching for passenger..."
    status_color = (0, 255, 255)  # Yellow (BGR format)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Perform verification every 10 frames to balance responsiveness and performance
        if counter % 10 == 0:
            try:
                # Perform facial recognition verification by comparing current frame with reference image
                # DeepFace will raise ValueError if no face is detected in either image
                result = DeepFace.verify(
                    img1_path=frame, 
                    img2_path=img_path,
                    model_name="Facenet",
                    detector_backend="opencv",  # Alternative: "mediapipe" for improved accuracy
                    distance_metric="cosine",
                    enforce_detection=True,  # Reject frames without detected faces
                    threshold=0.4  # Sensitivity threshold (lower = stricter matching)
                )
                
                # Update UI based on verification result
                if result["verified"]:
                    status_message = f"ACCESS GRANTED (Distance: {round(result['distance'], 2)})"
                    status_color = (0, 255, 0)  # Green
                else:
                    status_message = f"ACCESS DENIED (Distance: {round(result['distance'], 2)})"
                    status_color = (0, 0, 255)  # Red

            except ValueError:
                # Handle case where no face is detected in the frame
                status_message = "NO FACE DETECTED - Please reposition yourself"
                status_color = (0, 255, 255)  # Yellow
            except Exception as e:
                # Log any unexpected errors
                print(f"Unexpected error: {e}")

        counter += 1

        # Render user interface elements
        h, w, _ = frame.shape
        
        # Draw status bar at the top-left of the frame
        cv2.rectangle(frame, (0, 0), (400, 60), status_color, -1)
        
        # Select text color based on background for optimal visibility
        text_color = (0, 0, 0) if status_color == (0, 255, 255) else (255, 255, 255)
        cv2.putText(frame, status_message, (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, text_color, 2)

        # Display the processed frame
        cv2.imshow("AeroID - Secure Gate", frame)

        # Exit on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Cleanup resources
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    start_secure_gate()