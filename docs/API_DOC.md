# AeroID — API Documentation

**Base URL:** `http://localhost:8000`

---

## `GET /`

Health check & endpoint discovery.

**Response:**

```json
{
  "app_name": "AeroID",
  "message": "Welcome to the Face Recognition API!",
  "status": "System Online & Secure",
  "endpoints": {
    "docs": "/docs",
    "enroll": "/api/enroll",
    "verify": "/api/verify"
  }
}
```

---

## `POST /api/enroll`

Generates a compressed biometric vector from an encrypted face image. Used during registration (e.g. stored in QR code).

### Request Body

| Field             | Type     | Description                         |
| ----------------- | -------- | ----------------------------------- |
| `encrypted_image` | `string` | AES-encrypted, base64-encoded image |

```json
{
  "encrypted_image": "base64_encrypted_string..."
}
```

### Response — Success

| Field              | Type      | Description                                                   |
| ------------------ | --------- | ------------------------------------------------------------- |
| `message`          | `string`  | `"Received data successfully"`                                |
| `biometric_vector` | `object`  | Contains `status`, `biometric_vector` (compressed), `message` |
| `multiple_persons` | `boolean` | Always `false` when successful                                |

```json
{
  "message": "Received data successfully",
  "biometric_vector": {
    "status": "success",
    "biometric_vector": "compressed_base64_vector...",
    "message": null
  },
  "multiple_persons": false
}
```

### Response — YOLO Rejection (multiple persons / no person)

| Field              | Type      | Description                                               |
| ------------------ | --------- | --------------------------------------------------------- |
| `message`          | `string`  | Reason for rejection                                      |
| `biometric_vector` | `null`    | No vector generated                                       |
| `multiple_persons` | `boolean` | `true` if tailgating detected, `false` if no person found |

```json
{
  "message": "Multiple persons detected. Only one person is allowed.",
  "biometric_vector": null,
  "multiple_persons": true
}
```

```json
{
  "message": "No person detected in the frame.",
  "biometric_vector": null,
  "multiple_persons": false
}
```

### Response — DeepFace Error (no face found)

```json
{
  "message": "Received data successfully",
  "biometric_vector": {
    "status": "error",
    "message": "No face detected in the image."
  },
  "multiple_persons": false
}
```

### Response — Server Error

```json
{
  "message": "An error occurred during enrollment: ...",
  "biometric_vector": null
}
```

---

## `POST /api/verify`

Compares a live face image against a stored biometric vector (from QR code). Returns match/no-match with cosine distance.

### Request Body

| Field              | Type     | Description                                 |
| ------------------ | -------- | ------------------------------------------- |
| `encrypted_image`  | `string` | AES-encrypted, base64-encoded live image    |
| `biometric_vector` | `string` | Compressed biometric vector from enrollment |

```json
{
  "encrypted_image": "base64_encrypted_string...",
  "biometric_vector": "compressed_base64_vector..."
}
```

### Response — Success (Match)

| Field                  | Type      | Description                                |
| ---------------------- | --------- | ------------------------------------------ |
| `message`              | `string`  | `"Received data successfully"`             |
| `verification_results` | `object`  | Contains `is_match`, `distance`, `message` |
| `multiple_persons`     | `boolean` | Always `false` when successful             |

```json
{
  "message": "Received data successfully",
  "verification_results": {
    "is_match": true,
    "distance": 0.1842,
    "message": null
  },
  "multiple_persons": false
}
```

### Response — Success (No Match)

```json
{
  "message": "Received data successfully",
  "verification_results": {
    "is_match": false,
    "distance": 0.6035,
    "message": null
  },
  "multiple_persons": false
}
```

### Response — YOLO Rejection

```json
{
  "message": "Multiple persons detected. Only one person is allowed.",
  "verification_results": null,
  "multiple_persons": true
}
```

### Response — Server Error

```json
{
  "message": "An error occurred during verification: ...",
  "verification_results": null
}
```

---

## Processing Pipeline

Fiecare request trece prin două trepte:

```
Request → Decrypt Image
            │
            ▼
   ┌─────────────────┐
   │  Treapta 1: YOLO │  (YOLOv8n — fast, ~100ms)
   │  "The Bouncer"   │
   └────────┬────────┘
            │ ok?
      ┌─────┴─────┐
      │ NO        │ YES
      ▼           ▼
   Return      ┌──────────────────┐
   Error       │  Treapta 2:       │
               │  DeepFace/Facenet │  (~500ms)
               │  "The Detective"  │
               └────────┬─────────┘
                        ▼
                   Return Result
```

### Anti-Tailgating Logic (YOLO)

YOLO nu respinge orbește toate pozele cu mai multe persoane. Folosește **analiza ariei bounding box-urilor**:

- **Persoana cea mai mare** = pasagerul principal (cel mai aproape de cameră)
- **Persoane < 60% arie** față de principal = fundal → **ignorate**
- **Persoane ≥ 60% arie** = intrus la poartă → **TAILGATING ALERT** → reject

> Pragul de 60% este configurabil via `tailgate_ratio` în `YOLOFilter`.
