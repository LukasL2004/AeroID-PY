# vector_codec.py

import numpy as np
import base64
import gzip


def transform_vector_to_f16(biometric_vector):

    # Convert the biometric vector to a NumPy array
    vector_f16 = np.array(biometric_vector, dtype=np.float16)

    return vector_f16


def compress_vector(biometric_vector):

    # Convert the biometric vector to a NumPy array of float 16
    vector_f16 = transform_vector_to_f16(biometric_vector)

    # Convert in bytes
    vector_bytes = vector_f16.tobytes()

    # Arhive the bytes using gzip
    compressed_bytes = gzip.compress(vector_bytes)

    # Encode the compressed bytes to base64 for safe transmission (JSON)
    b64_string = base64.b64encode(compressed_bytes).decode('utf-8')

    return b64_string


def decompress_vector(b64_string):

    # Decode tghe base64 string to get the compressed bytes
    compressed_bytes = base64.b64decode(b64_string)

    # Decompress the bytes using gzip
    vector_bytes = gzip.decompress(compressed_bytes)

    # Convert the bytes back to a NumPy array of float16
    vector_f16 = np.frombuffer(vector_bytes, dtype=np.float16)

    # Convert the NumPy array back to a list of float32
    vector_f32 = vector_f16.astype(np.float32).tolist()

    return vector_f32