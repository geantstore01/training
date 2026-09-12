import hashlib
import secrets
import time
from uuid import UUID, uuid4


ROTATE = """
if redis.call('EXISTS', KEYS[1]) == 0 then return 'expired' end
if redis.call('HGET', KEYS[1], 'revoked') == '1' then return 'revoked' end
local current = redis.call('HGET', KEYS[1], 'digest')
if current ~= ARGV[1] then
  if redis.call('HEXISTS', KEYS[1], 'used:' .. ARGV[1]) == 1 then
    redis.call('HSET', KEYS[1], 'revoked', '1', 'digest', '')
    return 'reuse'
  end
  return 'invalid'
end
local rotations = tonumber(redis.call('HGET', KEYS[1], 'rotations') or '0')
if rotations >= 1000 then
  redis.call('HSET', KEYS[1], 'revoked', '1', 'digest', '')
  return 'expired'
end
redis.call('HSET', KEYS[1], 'used:' .. ARGV[1], '1', 'digest', ARGV[2], 'rotations', rotations+1)
return 'ok'
"""

CREATE = """
if redis.call('EXISTS', KEYS[1]) == 1 then return 0 end
redis.call('HSET', KEYS[1], 'user', ARGV[1], 'school', ARGV[2], 'version', ARGV[3],
  'digest', ARGV[4], 'revoked', '0', 'rotations', '0')
redis.call('EXPIRE', KEYS[1], ARGV[5])
return 1
"""

REVOKE = """
if redis.call('EXISTS', KEYS[1]) == 1 then redis.call('HSET', KEYS[1], 'revoked', '1', 'digest', '') end
return 1
"""


def session_key(sid):
    return f"edu:session:{{{UUID(str(sid))}}}"


def digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def unpack_refresh(token: str) -> UUID:
    if len(token) > 180:
        raise ValueError("Invalid refresh token")
    sid, secret = token.split(".", 1)
    if len(secret) != 64 or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in secret):
        raise ValueError("Invalid refresh token")
    return UUID(sid)


class SessionStore:
    def __init__(self, redis):
        self.redis = redis

    def create(self, user_id, school_id, version, ttl):
        sid = uuid4()
        token = f"{sid}.{secrets.token_urlsafe(48)}"
        if self.redis.eval(CREATE, 1, session_key(sid), str(user_id), str(school_id), str(version), digest(token), ttl) != 1:
            raise RuntimeError("Session identifier collision")
        return sid, token

    def read(self, sid):
        result = self.redis.hgetall(session_key(sid))
        return {key.decode(): value.decode() for key, value in result.items()}

    def rotate(self, token):
        sid = unpack_refresh(token)
        new = f"{sid}.{secrets.token_urlsafe(48)}"
        status = self.redis.eval(ROTATE, 1, session_key(sid), digest(token), digest(new)).decode()
        return status, new

    def revoke(self, sid):
        self.redis.eval(REVOKE, 1, session_key(sid))
