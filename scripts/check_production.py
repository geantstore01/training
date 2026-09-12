"""Validate rendered Compose JSON from stdin; never print resolved environment."""
import json
import re
import sys


def main():
    config = json.load(sys.stdin)
    services = config["services"]
    domain = services["traefik"]["environment"]["EDU_DOMAIN"]
    if not re.fullmatch(r"(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}",domain):
        raise SystemExit("Invalid public domain")
    if domain.endswith((".invalid",".test",".localhost",".example")):
        raise SystemExit("A real public domain is required")
    if services["web"]["environment"]["COOKIE_SECURE"] != "true":
        raise SystemExit("Secure cookies required")
    for name,service in services.items():
        for port in service.get("ports",[]):
            if name != "traefik" and port.get("host_ip") != "127.0.0.1":
                raise SystemExit("Unexpected public port: " + name)
    print("Production configuration preflight passed. DNS, NAT, TLS and legal checks remain separate.")


if __name__ == "__main__": main()
