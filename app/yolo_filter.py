# yolo_filter.py
# Treapta 1 – "The Bouncer"
# Fast YOLOv8n pre-filter for The Smart Corridor.
# Scans the frame and rejects images with 0 or 2+ persons.

from ultralytics import YOLO


class YOLOFilter:
    PERSON_CLASS_ID = 0  # COCO class id for "person"

    def __init__(self, model_path="yolov8n.pt", confidence=0.40, tailgate_ratio=0.60):
        self.model = YOLO(model_path)
        self.confidence = confidence
        self.tailgate_ratio = tailgate_ratio  # Area ratio threshold for intruder alert
        print(f"[YOLO] Model loaded: {model_path} (conf={confidence}, tailgate={tailgate_ratio:.0%})")


    def scan_frame(self, img):
        """
        Run YOLOv8n on the image and apply anti-tailgating logic.

        Instead of simply counting persons, we compare bounding box areas:
        - Largest person = main passenger (closest to camera)
        - Others with area < BACKGROUND_RATIO of main = background noise → ignored
        - Others with area >= TAILGATE_RATIO of main = intruder → security alert

        Args:
            img: file path (str) or numpy array (cv2 image)

        Returns:
            dict with keys: ok (bool), persons_found (int), message (str | None)
        """
        try:
            results = self.model(img, conf=self.confidence, verbose=False)

            # Filter detections for "person" class only
            persons = []
            for result in results:
                for box in result.boxes:
                    if int(box.cls[0]) == self.PERSON_CLASS_ID:
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        width = x2 - x1
                        height = y2 - y1
                        area = width * height
                        persons.append({"box": box, "area": area})

            count = len(persons)

            # ── No person detected ──────────────────────────────────────
            if count == 0:
                print("[YOLO] No person detected in the frame.")
                return {
                    "ok": False,
                    "persons_found": 0,
                    "message": "No person detected in the frame."
                }

            # ── Single person → perfect ─────────────────────────────────
            if count == 1:
                print("[YOLO] OK – exactly 1 person detected.")
                return {
                    "ok": True,
                    "persons_found": 1,
                    "message": None
                }

            # ── Multiple persons → anti-tailgating analysis ─────────────
            # Sort by area descending: index 0 = main passenger (largest)
            persons.sort(key=lambda p: p["area"], reverse=True)
            main_area = persons[0]["area"]

            intruders = 0
            background = 0

            for other in persons[1:]:
                ratio = other["area"] / main_area
                if ratio >= self.tailgate_ratio:
                    # Close intruder – too large to be background
                    intruders += 1
                    print(f"[YOLO] ⚠ Intruder detected (area ratio: {ratio:.1%} >= {self.tailgate_ratio:.0%})")
                else:
                    # Background person – harmless
                    background += 1
                    print(f"[YOLO] Background person ignored (area ratio: {ratio:.1%})")

            if intruders > 0:
                print(f"[YOLO] TAILGATING ALERT – {intruders} intruder(s) near the gate. Rejecting.")
                return {
                    "ok": False,
                    "persons_found": count,
                    "message": "Multiple persons detected. Only one person is allowed."
                }

            # All other persons are background noise
            print(f"[YOLO] OK – 1 main passenger + {background} background person(s) ignored.")
            return {
                "ok": True,
                "persons_found": 1,
                "message": None
            }

        except Exception as e:
            print(f"[YOLO] Error during scan: {e}")
            return {
                "ok": False,
                "persons_found": 0,
                "message": f"YOLO scan failed: {str(e)}"
            }

