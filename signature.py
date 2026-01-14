import hashlib
import hmac
import time
from typing import Dict
from fastapi import Request, Depends, HTTPException, status
from models import User
from auth import get_current_user

nonce_cache: Dict[str, float] = {}
NONCE_TTL = 300

def compute_body_hash(body: bytes) -> str:
    if not body:
        return ''
    return hashlib.sha256(body).hexdigest()

async def verify_signature(request: Request, current_user: User = Depends(get_current_user)):
    signature = request.headers.get("X-Signature")
    timestamp_str = request.headers.get("X-Timestamp")
    nonce = request.headers.get("X-Nonce")

    if not all([signature, timestamp_str, nonce]):
        return current_user

    try:
        timestamp = int(timestamp_str)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid timestamp")

    current_time = int(time.time())
    if abs(current_time - timestamp) > 60:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Timestamp expired or invalid")

    if nonce in nonce_cache:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Replay detected")
    nonce_cache[nonce] = current_time + NONCE_TTL

    to_remove = [n for n, exp in nonce_cache.items() if current_time > exp]
    for n in to_remove:
        del nonce_cache[n]

    method = request.method.upper()
    path = request.url.path
    query_params = '&'.join([f"{k}={v}" for k, v in sorted(request.query_params.items())])
    body = await request.body()
    body_hash = compute_body_hash(body)
    message = f"{method}|{path}|{query_params}|{body_hash}|{timestamp}|{nonce}"

    expected_signature = hmac.new(
        current_user.api_key.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    return current_user
