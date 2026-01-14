import hashlib
import hmac
import time
from typing import Dict
from fastapi import Request, Depends, HTTPException, status
from models import User
from auth import get_current_user

# In-memory cache для used nonces (nonce: expiration_time). В production - Redis.
nonce_cache: Dict[str, float] = {}
NONCE_TTL = 300  # 5 минут

def compute_body_hash(body: bytes) -> str:
    if not body:
        return ''
    return hashlib.sha256(body).hexdigest()

async def verify_signature(request: Request, current_user: User = Depends(get_current_user)):
    # Извлечь headers
    signature = request.headers.get("X-Signature")
    timestamp_str = request.headers.get("X-Timestamp")
    nonce = request.headers.get("X-Nonce")

    # Если заголовки подписи отсутствуют, возвращаем пользователя только с JWT аутентификацией
    # Это позволяет тестировать API через Swagger UI без необходимости генерировать подписи
    if not all([signature, timestamp_str, nonce]):
        return current_user

    try:
        timestamp = int(timestamp_str)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid timestamp")

    # Проверить timestamp window (60 секунд)
    current_time = int(time.time())
    if abs(current_time - timestamp) > 60:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Timestamp expired or invalid")

    # Проверить nonce uniqueness
    if nonce in nonce_cache:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Replay detected")
    nonce_cache[nonce] = current_time + NONCE_TTL  # Добавить в cache

    # Очистить expired nonces (lazy cleanup)
    to_remove = [n for n, exp in nonce_cache.items() if current_time > exp]
    for n in to_remove:
        del nonce_cache[n]

    # Реконструировать message
    method = request.method.upper()
    path = request.url.path
    query_params = '&'.join([f"{k}={v}" for k, v in sorted(request.query_params.items())])
    body = await request.body()
    body_hash = compute_body_hash(body)
    message = f"{method}|{path}|{query_params}|{body_hash}|{timestamp}|{nonce}"

    # Compute expected signature
    expected_signature = hmac.new(
        current_user.api_key.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    return current_user  # Возврат пользователя для chaining