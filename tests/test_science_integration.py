"""Real PostgreSQL checks; enabled only with EDU_TEST_INTEGRATION=1 on Compose."""
from uuid import uuid4
from sqlalchemy import text
from shared.security.crypto import IdentityCipher

def test_science_notebook_rls_and_ciphertext(db,identities,tmp_path):
    import json,secrets,base64
    keyfile=tmp_path/"keys.json"
    keyfile.write_text(json.dumps({"active":"v1","keys":{"v1":base64.b64encode(secrets.token_bytes(32)).decode()}}))
    # Database isolation does not rely on any text field or client-provided owner.
    row_id=uuid4()
    cipher=IdentityCipher(keyfile)
    blob=cipher.encrypt({"hypothesis":"La lampe s’allume.","conclusion":""},school_id=identities["tenant"],owner_id=row_id,purpose="science-notebook")
    db.execute(text("""INSERT INTO science_runs(id,tenant_id,student_id,request_id,chapter,setting,notebook_ciphertext,observation,expires_at)
        VALUES (:id,:tenant,:student,:request,'circuits','ferme',:cipher,'{}',now()+interval '30 days')"""),
        {"id":row_id,"tenant":identities["tenant"],"student":identities["student"],"request":uuid4(),"cipher":blob})
    db.execute(text("SET LOCAL ROLE edu_assessment"))
    assert db.scalar(text("SELECT count(*) FROM science_runs WHERE id=:id"),{"id":row_id})==1
    stored=db.scalar(text("SELECT notebook_ciphertext FROM science_runs WHERE id=:id"),{"id":row_id})
    assert b"lampe" not in stored
    assert cipher.decrypt(stored,school_id=identities["tenant"],owner_id=row_id,purpose="science-notebook")["hypothesis"]=="La lampe s’allume."
    db.execute(text("SELECT set_config('app.tenant_id',:tenant,true)"),{"tenant":str(identities["other"])})
    assert db.scalar(text("SELECT count(*) FROM science_runs WHERE id=:id"),{"id":row_id})==0
