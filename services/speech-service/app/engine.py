import io
import subprocess
import wave
from shared.ai.transport import DependencyFailure

def synthesize(value):
    try:
        result=subprocess.run(["espeak-ng","-v","fr-fr","-s","145","--stdout","--stdin"],input=value.encode("utf-8"),capture_output=True,timeout=15,check=True)
        # espeak streaming WAV has an unknown RIFF length. Rebuild a finite WAV in memory.
        with wave.open(io.BytesIO(result.stdout),"rb") as source:
            params=source.getparams();frames=source.readframes(2_000_000)
        output=io.BytesIO()
        with wave.open(output,"wb") as target:
            target.setparams(params);target.writeframes(frames)
        if len(output.getvalue())>4_000_000:raise ValueError("size")
        return output.getvalue()
    except (OSError,subprocess.SubprocessError,wave.Error,ValueError):
        raise DependencyFailure("speech_unavailable") from None
