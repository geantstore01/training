"""Root timer: aggregate GPU metrics only, no process names or command lines."""
from pathlib import Path
import csv
import subprocess
import time
from datetime import datetime, timedelta, timezone
import re


def purge_technical_logs(logs, now):
    threshold = (now - timedelta(days=6)).strftime("%Y%m%d")
    for path in logs.glob("*/*.jsonl*"):
        match = re.fullmatch(r"[a-z-]+-service\.([0-9]{8})\.jsonl(?:\.[12])?", path.name)
        if match and match[1] < threshold and not path.is_symlink() and logs.resolve() in path.resolve().parents:
            path.unlink(missing_ok=True)


def main():
    target = Path(__file__).resolve().parents[1] / "runtime/metrics/host.prom"
    target.parent.mkdir(parents=True,exist_ok=True)
    lines = [f"edu_host_metrics_timestamp_seconds {time.time()}"]
    try:
        output = subprocess.run(["nvidia-smi", "--query-gpu=index,utilization.gpu,memory.used,temperature.gpu", "--format=csv,noheader,nounits"],
            check=True,capture_output=True,text=True,timeout=8)
        for row in csv.reader(output.stdout.splitlines()):
            index, load, memory, temperature = (float(x.strip()) for x in row)
            for name, value in (("utilization_percent",load),("memory_used_bytes",memory*1024*1024),("temperature_celsius",temperature)):
                lines.append(f'edu_gpu_{name}{{gpu="{int(index)}"}} {value}')
        lines.append("edu_gpu_collection_success 1")
    except (OSError, subprocess.SubprocessError, ValueError):
        lines.append("edu_gpu_collection_success 0")
    temp = target.with_suffix(".tmp")
    temp.write_text("\n".join(lines)+"\n")
    temp.chmod(0o644)
    temp.replace(target)
    logs = target.parents[1] / "telemetry"
    purge_technical_logs(logs, datetime.now(timezone.utc))


if __name__ == "__main__": main()
