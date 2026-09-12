"""Téléchargement HTTPS officiel, IP publique épinglée et extraction isolée."""
import http.client
import ipaddress
import re
import socket
import ssl
import certifi
import subprocess
import sys
import unicodedata
from urllib.parse import urlsplit
from shared.ai.transport import DependencyFailure

# Référentiels publiés par le ministère, dont l'archive de programmes sous
# Licence Ouverte diffusée sur data.gouv.fr.
HOSTS = {"formation-civique.interieur.gouv.fr", "www.senat.fr", "european-union.europa.eu", "education.gouv.fr", "www.education.gouv.fr", "eduscol.education.gouv.fr", "data.gouv.fr", "www.data.gouv.fr", "static.data.gouv.fr"}
MAX_BYTES = 2_000_000

def official_url(url):
    try:
        parsed = urlsplit(url)
        valid = parsed.scheme == "https" and parsed.hostname in HOSTS and parsed.port in {None, 443} and not parsed.username and not parsed.password and not parsed.fragment
    except ValueError:
        valid = False
    if not valid or not url.isascii() or len(url) > 2000 or any(ord(c) < 33 for c in url):
        raise ValueError("URL officielle HTTPS requise")
    return parsed

def fetch(url):
    parsed = official_url(url)
    try:
        addresses = socket.getaddrinfo(parsed.hostname, 443, type=socket.SOCK_STREAM)
        if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
            raise DependencyFailure("document_address_denied")
        raw = socket.create_connection((addresses[0][4][0], 443), timeout=8)
        connection = http.client.HTTPSConnection(parsed.hostname, timeout=8)
        try:
            context = ssl.create_default_context()
            # Add the pinned dependency's public CA bundle on hosts whose system
            # store lacks an issuer; certificate and hostname checks stay enabled.
            context.load_verify_locations(cafile=certifi.where())
            connection.sock = context.wrap_socket(raw, server_hostname=parsed.hostname)
            connection.request("GET", (parsed.path or "/") + ("?" + parsed.query if parsed.query else ""), headers={"User-Agent": "Educapilote-document-ingestion/1.0", "Accept-Encoding": "identity"})
            response = connection.getresponse()
            if response.status != 200:
                raise DependencyFailure("document_http_or_redirect")
            mime = response.getheader("Content-Type", "").split(";")[0].strip().lower()
            if mime not in {"application/pdf", "text/plain", "text/html", "text/markdown"}:
                raise DependencyFailure("document_type")
            data = response.read(MAX_BYTES + 1)
            if len(data) > MAX_BYTES:
                raise DependencyFailure("document_size")
            return data, mime
        finally:
            connection.close()
            raw.close()
    except (OSError, http.client.HTTPException):
        raise DependencyFailure("document_unavailable") from None

def extract(data, mime, pages=None, profile="full"):
    import json
    try:
        result = subprocess.run([sys.executable, "-m", "shared.ai.extract_document", mime, json.dumps(pages or []), profile], input=data, capture_output=True, timeout=12, check=True)
        return clean(result.stdout.decode("utf-8"))
    except (subprocess.SubprocessError, UnicodeError, ValueError):
        raise DependencyFailure("document_extraction") from None

def clean(value):
    value = unicodedata.normalize("NFKC", value)
    value = "".join(c for c in value if c in "\n\t" or not unicodedata.category(c).startswith("C"))
    value = re.sub(r"[^\S\n]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value).strip()
    if not 80 <= len(value) <= 100_000:
        raise ValueError("Document vide, trop court ou trop long")
    return value

def chunks(value):
    units = re.split(r"\n\s*\n|(?<=[.!?])\s+", value)
    output, current = [], ""
    for unit in units:
        for word in unit.split():
            if len(word) > 300:
                raise ValueError("Mot anormalement long")
            if len(current) + len(word) + 1 > 1600:
                output.append(current)
                current = " ".join(current.split()[-20:])
            current = (current + " " + word).strip()
        if current and len(current) > 900:
            output.append(current)
            current = ""
    if current:
        output.append(current)
    if not output or len(output) > 100:
        raise ValueError("Nombre de passages invalide")
    return output
