from datetime import datetime,timedelta,timezone
from pathlib import Path
import io,json,wave
from unittest.mock import Mock
import pytest
from pydantic import ValidationError
from shared.progression import minutes
from shared.service_loader import load_service
from shared.ai.transport import DependencyFailure

load_service("speech-service");load_service("notification-service")
from edu_speech_service import engine
from edu_notification_service.routes import JobInput

def test_session_duration_clips_window_overlap_and_idle_cap():
    start=datetime(2026,1,1,tzinfo=timezone.utc);end=start+timedelta(days=1)
    assert minutes([(start,start+timedelta(minutes=20)),(start+timedelta(minutes=10),start+timedelta(hours=3))],start,end)==40
    assert minutes([(start-timedelta(hours=2),start+timedelta(hours=1))],start,end)==0
    assert minutes([(start,None)],start,end)==0

def test_tts_uses_memory_and_stdin(monkeypatch,tmp_path):
    data=io.BytesIO()
    with wave.open(data,"wb") as w:w.setparams((1,2,22050,0,"NONE","not compressed"));w.writeframes(b'\0\0'*2205)
    call=Mock(return_value=Mock(stdout=data.getvalue()))
    monkeypatch.setattr(engine.subprocess,"run",call)
    result=engine.synthesize("Lis la consigne.")
    with wave.open(io.BytesIO(result)) as w:assert w.getnframes()==2205
    args,kwargs=call.call_args
    assert '--stdin' in args[0] and 'Lis la consigne.' not in args[0]
    assert kwargs['input']==b'Lis la consigne.' and not list(tmp_path.iterdir())

def test_tts_failure_does_not_expose_command_or_input(monkeypatch):
    monkeypatch.setattr(engine.subprocess,"run",Mock(side_effect=OSError("private-input")))
    with pytest.raises(DependencyFailure,match="speech_unavailable") as exc:engine.synthesize("private-input")
    assert 'private-input' not in str(exc.value)

def test_batch_cannot_be_empty_or_add_tenant():
    from uuid import uuid4
    with pytest.raises(ValidationError):JobInput(kind="exercise_batch",idempotency_key=uuid4())
    with pytest.raises(ValidationError):JobInput(kind="weekly_reports",idempotency_key=uuid4(),tenant_id=uuid4())

def test_n8n_workflows_are_inactive_authenticated_and_do_not_save_payloads():
    files=list(Path('workflows/n8n').glob('*.json'))
    # Docker test image includes workflows as part of its reproducible configuration.
    assert len(files)==4
    for path in files:
        value=json.loads(path.read_text(encoding='utf-8'))
        assert value['active'] is False
        assert value['settings']['timezone']=='Europe/Paris'
        assert value['settings']['saveDataSuccessExecution']=='none'
        for node in value['nodes']:
            if node['type'].endswith('webhook'):assert node['parameters']['authentication']=='headerAuth'
            if node['type'].endswith('httpRequest'):assert node['parameters']['genericAuthType']=='httpHeaderAuth'
