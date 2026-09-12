"""Recette HTTP du frontend déployé, sans créer de compte ni donnée pédagogique."""
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError

base="http://127.0.0.1:18088"
with urlopen(base+"/connexion",timeout=15) as response:
    body=response.read().decode()
    assert response.status==200 and "Prêt pour la suite" in body
    assert "nonce-" in response.headers["Content-Security-Policy"]
    assert "no-store" in response.headers["Cache-Control"]
with urlopen(base+"/eleve",timeout=15) as response:
    assert response.url.endswith("/connexion")
for path,method,origin,status in [("/api/session","GET",None,401),("/api/session","POST","https://example.invalid",403),("/api/ai-router/plan","POST",base,404)]:
    request=Request(base+path,method=method,data=b"{}" if method=="POST" else None,headers={"Content-Type":"application/json",**({"Origin":origin} if origin else {})})
    try:
        with urlopen(request,timeout=15) as response:assert response.status==status
    except HTTPError as error:assert error.code==status,(path,error.code)
print(json.dumps({"frontend":True,"protected_redirect":True,"opaque_session_required":True,"csrf_rejected":True,"internal_route_blocked":True,"csp_nonce":True}))
