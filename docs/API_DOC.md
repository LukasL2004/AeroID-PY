# AeroID - Backend Python API Documentation

---

## 1. Passenger Enroll
**Endpoint:** `POST /api/enroll`

This endpoint receives an encrypted image of the passenger, extracts the face, and returns a JSON with biometric data.

---

</br>

**Request Body**
```json
{
    "encrypted_image": "gAAAAABpl... (encrypted image)"
}
```

---

</br>

**Response JSON**

```json

{
    "message": "Received data successfully",
    "biometric_vector": {
        "status": "success",
        "biometric_vector": [
            -0.18290872871875763,
        ]
    }
}
```

</br>

## 2. Passenger Verify (Smart Corridor Checkpoint)
**Endpoint:** `POST /api/verify`

This endpoint is called when the passenger passes through the physical gate. It receives the live captured photo and the biometric vector from the QR code, comparing them to verify identity.

---

</br>

**Request Body**
```json

{
    "biometric_vector": [-0.18290872871875763 ],
    "encrypted_image": "gAAAAABpmFSJ0lccU_lQVCSgedjkc_4Vf0i"

}
```

---

</br>

**Response Body**
```json
{
    "message": "Received data successfully",
    "verification_results": {
        "is_match": true,
        "distance": 0.3385162339880272,
        "message": null
    }
}
```