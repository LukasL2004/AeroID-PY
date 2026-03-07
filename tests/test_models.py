# test_models.py
# DeepFace model evaluation — runs face detection on every image in assets/imgs/
# and reports a detection success rate score.
#
# Usage:
#   python tests/test_models.py
#
# To compare models, manually update model_name / detector in app/face_engine.py
# and re-run this script.

import sys
import io
import re
import time
import glob
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Add the project root to PATH for local imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.face_engine import FaceEngine
from app.yolo_filter import YOLOFilter


def collect_images(imgs_dir: str):
    """Collect all .jpg and .jpeg files from the specified directory."""
    patterns = ["*.jpg", "*.jpeg"]
    images = []
    for pat in patterns:
        images.extend(glob.glob(str(Path(imgs_dir) / pat)))
    return sorted(set(images))  # deduplicate in case a file matches both globs


def group_images_by_person(images):
    """
    Group image paths by person name based on the naming convention: Name_N.jpg
    e.g. AndreiT_1.jpg, AndreiT_2.jpg → { "AndreiT": { 1: path, 2: path } }
    """
    groups = defaultdict(dict)
    pattern = re.compile(r"^(.+)_(\d+)$")  # matches "Name_N" (without extension)

    for img_path in images:
        stem = Path(img_path).stem  # filename without extension
        match = pattern.match(stem)
        if match:
            person_name = match.group(1)
            index = int(match.group(2))
            groups[person_name][index] = img_path

    return dict(groups)


def run_test():
    project_root = Path(__file__).parent.parent
    imgs_dir = project_root / "assets" / "imgs"

    if not imgs_dir.exists():
        print(f"[ERROR] Directory '{imgs_dir}' does not exist. Add images and try again.")
        sys.exit(1)

    images = collect_images(str(imgs_dir))

    if not images:
        print(f"[ERROR] No .jpg/.jpeg files found in '{imgs_dir}'.")
        sys.exit(1)

    # Instantiate FaceEngine with its current configuration
    engine = FaceEngine()
    yolo_filter = YOLOFilter()
    model_name = engine.model_name
    detector = engine.detector

    print("=" * 65)
    print(f"  DeepFace MODEL EVALUATION")
    print(f"  Model:    {model_name}")
    print(f"  Detector: {detector}")
    print(f"  Images:   {len(images)}")
    print("=" * 65)

    successes = 0
    failures = 0
    failed_images = []
    times = []

    for idx, img_path in enumerate(images, start=1):
        img_name = Path(img_path).name
        print(f"\n[{idx}/{len(images)}] {img_name} ... ", end="", flush=True)

        start = time.time()

        # Treapta 1: YOLO scan
        scan = yolo_filter.scan_frame(img_path)
        if not scan["ok"]:
            elapsed = time.time() - start
            times.append(elapsed)
            failures += 1
            failed_images.append((img_name, scan["message"]))
            print(f"✗  ({elapsed:.2f}s)  — [YOLO] {scan['message']}")
            continue

        # Treapta 2: DeepFace
        result = engine.generate_vector(img_path)
        elapsed = time.time() - start

        times.append(elapsed)

        if result["status"] == "success":
            successes += 1
            print(f"✓  ({elapsed:.2f}s)")
        else:
            failures += 1
            failed_images.append((img_name, result.get("message", "unknown")))
            print(f"✗  ({elapsed:.2f}s)  — {result.get('message', '')}")

    # ────────────────── SUMMARY ──────────────────
    total = len(images)
    score = (successes / total) * 100 if total > 0 else 0
    avg_time = sum(times) / len(times) if times else 0

    print("\n")
    print("=" * 65)
    print(f"  RESULTS — {model_name} + {detector}")
    print("-" * 65)
    print(f"  Total images tested   : {total}")
    print(f"  Successful detections : {successes}")
    print(f"  Failed detections     : {failures}")
    print(f"  Detection score       : {score:.1f}%")
    print(f"  Avg time / image      : {avg_time:.2f}s")
    print("=" * 65)

    if failed_images:
        print("\n  Failed images:")
        for name, reason in failed_images:
            print(f"    ✗ {name}  —  {reason}")
        print()


def run_verification():
    """
    Identity verification test.
    Groups images by person (Name_1.jpg, Name_2.jpg, ...),
    generates a vector for _1, then compares it against every other
    image of the same person using FaceEngine.compare_vectors().
    """
    project_root = Path(__file__).parent.parent
    imgs_dir = project_root / "assets" / "imgs"
    images = collect_images(str(imgs_dir))
    groups = group_images_by_person(images)

    if not groups:
        print("\n[SKIP] No images matching the Name_N pattern found. Skipping verification.")
        return

    engine = FaceEngine()
    model_name = engine.model_name
    detector = engine.detector

    print("\n")
    print("=" * 65)
    print(f"  IDENTITY VERIFICATION TEST")
    print(f"  Model:    {model_name}")
    print(f"  Detector: {detector}")
    print(f"  Persons:  {len(groups)}")
    print("=" * 65)

    total_comparisons = 0
    total_matches = 0
    total_mismatches = 0
    total_errors = 0
    person_results = []

    for person, idx_map in sorted(groups.items()):
        if 1 not in idx_map:
            print(f"\n  [SKIP] {person}: no _1 reference image found.")
            continue

        other_indices = sorted([i for i in idx_map if i != 1])
        if not other_indices:
            print(f"\n  [SKIP] {person}: only _1 image found, nothing to compare.")
            continue

        print(f"\n  ┌─ {person} ({len(other_indices)} comparison(s))")

        # Generate the reference vector from _1
        ref_path = idx_map[1]
        ref_result = engine.generate_vector(ref_path)

        if ref_result["status"] != "success":
            print(f"  │  ✗ {person}_1 — failed to generate reference vector")
            total_errors += len(other_indices)
            person_results.append((person, 0, len(other_indices), 0))
            print(f"  └─ Score: 0/{len(other_indices)}")
            continue

        ref_vector = ref_result["biometric_vector"]
        matches = 0
        mismatches = 0
        errors = 0

        for idx in other_indices:
            compare_path = idx_map[idx]
            compare_name = Path(compare_path).name
            total_comparisons += 1

            # Generate vector for the comparison image
            cmp_result = engine.generate_vector(compare_path)

            if cmp_result["status"] != "success":
                print(f"  │  ✗ {compare_name} — detection failed")
                errors += 1
                continue

            cmp_vector = cmp_result["biometric_vector"]

            # Compare vectors
            match_result = engine.compare_vectors(ref_vector, cmp_vector)

            is_match = match_result["is_match"]
            distance = match_result["distance"]

            if is_match:
                matches += 1
                print(f"  │  ✓ {compare_name}  —  MATCH  (distance: {distance:.4f})")
            else:
                mismatches += 1
                print(f"  │  ✗ {compare_name}  —  NO MATCH  (distance: {distance:.4f})")

        total_matches += matches
        total_mismatches += mismatches
        total_errors += errors
        person_results.append((person, matches, mismatches, errors))
        print(f"  └─ Score: {matches}/{matches + mismatches + errors}")

    # ────────────────── VERIFICATION SUMMARY ──────────────────
    print("\n")
    print("=" * 65)
    print(f"  VERIFICATION RESULTS — {model_name} + {detector}")
    print("-" * 65)
    print(f"  Total comparisons     : {total_comparisons}")
    print(f"  Matches               : {total_matches}")
    print(f"  Mismatches            : {total_mismatches}")
    print(f"  Errors (no face)      : {total_errors}")
    if total_comparisons > 0:
        match_rate = (total_matches / total_comparisons) * 100
        print(f"  Match rate            : {match_rate:.1f}%")
    print("-" * 65)

    # Per-person breakdown
    print(f"  {'Person':<20} {'Match':>6} {'Fail':>6} {'Error':>6}")
    print(f"  {'─' * 20} {'─' * 6} {'─' * 6} {'─' * 6}")
    for person, m, f, e in person_results:
        print(f"  {person:<20} {m:>6} {f:>6} {e:>6}")
    print("=" * 65)


class TeeWriter:
    """Duplicates writes to both the original stdout and a StringIO buffer."""

    def __init__(self, original):
        self.original = original
        self.buffer = io.StringIO()

    def write(self, text):
        self.original.write(text)
        self.buffer.write(text)

    def flush(self):
        self.original.flush()

    def get_log(self):
        return self.buffer.getvalue()


def save_results(log_content: str):
    """Save the full test log to tests/model_tests/ with a descriptive filename."""
    engine = FaceEngine()
    model = engine.model_name
    detector = engine.detector
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_dir = Path(__file__).parent / "model_tests"
    output_dir.mkdir(exist_ok=True)

    filename = f"{model}_{detector}_{timestamp}.txt"
    filepath = output_dir / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(log_content)

    print(f"\n[SAVED] Results written to: {filepath}")


def run_yolo_test():
    """
    YOLO multi-person test.
    Scans all Persoane_*.jpg/jpeg images from assets/imgs/ and reports
    how many persons YOLO detected in each.
    These images should contain >=2 persons to test rejection.
    """
    project_root = Path(__file__).parent.parent
    imgs_dir = project_root / "assets" / "imgs"

    # Collect Persoane_* images
    patterns = ["Persoane_*.jpg", "Persoane_*.jpeg", "Persoane_*.JPG", "Persoane_*.JPEG"]
    images = []
    for pat in patterns:
        images.extend(glob.glob(str(imgs_dir / pat)))
    images = sorted(set(images))

    if not images:
        print("\n[SKIP] No Persoane_* images found. Add images to test multi-person rejection.")
        return

    yolo_filter = YOLOFilter()

    print("\n")
    print("=" * 65)
    print(f"  YOLO MULTI-PERSON TEST")
    print(f"  Images:   {len(images)}")
    print("=" * 65)

    correctly_rejected = 0
    incorrectly_passed = 0

    for idx, img_path in enumerate(images, start=1):
        img_name = Path(img_path).name
        print(f"\n  [{idx}/{len(images)}] {img_name} ... ", end="", flush=True)

        scan = yolo_filter.scan_frame(img_path)

        if not scan["ok"]:
            correctly_rejected += 1
            print(f"✓ REJECTED — {scan['persons_found']} person(s) — {scan['message']}")
        else:
            incorrectly_passed += 1
            print(f"✗ PASSED (should have been rejected) — {scan['persons_found']} person(s)")

    # Summary
    total = len(images)
    print("\n")
    print("-" * 65)
    print(f"  Correctly rejected    : {correctly_rejected}/{total}")
    print(f"  Incorrectly passed    : {incorrectly_passed}/{total}")
    print("=" * 65)


if __name__ == "__main__":
    tee = TeeWriter(sys.stdout)
    sys.stdout = tee

    try:
        run_test()
        run_verification()
        run_yolo_test()
    finally:
        sys.stdout = tee.original

    save_results(tee.get_log())
