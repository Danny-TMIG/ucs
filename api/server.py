from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ucs.models.local_mlx import LocalMLXModel, MLX_AVAILABLE
from ucs.ledger.worm import WORMLedger
from ucs.governance.gates import ExecutiveGovernance
from ucs.config.settings import settings
import pathlib
import json

app = FastAPI(title="UCS Frontier Control Plane", version="1.0.0")
security = HTTPBearer(auto_error=False)

TOKENS_PATH = pathlib.Path.home() / ".ucs" / "tokens" / "aether.json"

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    if not TOKENS_PATH.exists():
        return True
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    try:
        tokens_data = json.loads(TOKENS_PATH.read_text())
        valid_tokens = [t.get("token") for t in tokens_data]
        if credentials.credentials not in valid_tokens:
            raise HTTPException(status_code=403, detail="Invalid authorization token")
    except Exception:
        pass
    return True

model = LocalMLXModel(settings.model_path)
ledger = WORMLedger(settings.worm_ledger_path)
governance = ExecutiveGovernance()

@app.get("/health")
def health(authorized: bool = Depends(verify_token)):
    ledger.append("health_check", {"mlx_available": MLX_AVAILABLE})
    return {
        "status": "healthy",
        "model": settings.model_path,
        "mlx_available": MLX_AVAILABLE,
        "ledger_integrity": ledger.verify_integrity()
    }

@app.post("/infer")
def infer(prompt: str, max_tokens: int = 128, authorized: bool = Depends(verify_token)):
    governance.assert_no_veto()
    if not MLX_AVAILABLE:
        raise HTTPException(status_code=503, detail="MLX runtime environment unavailable")
    res = model.generate(prompt, max_tokens=max_tokens)
    ledger.append("inference", {"prompt": prompt, "tokens": max_tokens})
    return res
