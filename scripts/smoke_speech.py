"""À exécuter dans l'image speech : vraie synthèse locale, sans donnée d'élève."""
import io
import wave

from app.engine import synthesize

audio = synthesize("Lis la consigne puis explique ta démarche.")
with wave.open(io.BytesIO(audio)) as wav:
    assert wav.getnframes() > 1000
    assert wav.getnchannels() == 1
    print({"bytes": len(audio), "frames": wav.getnframes(), "sample_rate": wav.getframerate()})
