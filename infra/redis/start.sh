#!/bin/sh
set -eu
password="$(cat /run/secrets/redis_password)"
case "$password" in *[!a-zA-Z0-9]*|'') echo 'Invalid Redis secret format' >&2; exit 1;; esac
umask 077
printf 'user default on >%s ~cache:* &cache:* +@all -@dangerous +ping\n' "$password" > /tmp/users.acl
for role in auth user safety curriculum content exercise assessment tutor retrieval ai-router class analytics admin speech notification; do
  password="$(cat /run/secrets/redis_$role)"
  case "$password" in *[!a-zA-Z0-9]*|'') echo 'Invalid Redis secret format' >&2; exit 1;; esac
  if [ "$role" = auth ]; then
    printf 'user edu_auth on >%s ~edu:session:* ~edu:rate:auth:* +ping +select +hello +client|setinfo +eval +exists +hset +hget +hgetall +hexists +expire +incr +del\n' "$password" >> /tmp/users.acl
  elif [ "$role" = notification ]; then
    printf 'user edu_notification on >%s %%R~edu:session:* %%RW~edu:rate:notification:* %%RW~edu:jobs:* +ping +select +hello +client|setinfo +hgetall +hget +eval +incr +expire +lpush +blpop\n' "$password" >> /tmp/users.acl
  else
    printf 'user edu_%s on >%s %%R~edu:session:* %%RW~edu:rate:%s:* +ping +select +hello +client|setinfo +hgetall +hget +eval +incr +expire\n' "$role" "$password" "$role" >> /tmp/users.acl
  fi
done
password="$(cat /run/secrets/redis_web)"
case "$password" in *[!a-zA-Z0-9]*|'') exit 1;; esac
printf 'user edu_web on >%s ~edu:web:* +ping +hello +client|setinfo +get +set +del +eval +expire\n' "$password" >> /tmp/users.acl
exec redis-server /etc/redis/redis.conf --aclfile /tmp/users.acl
