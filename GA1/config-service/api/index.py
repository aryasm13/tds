import os
from pathlib import Path

import yaml
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

ROOT = Path(__file__).resolve().parent.parent
PREFIX = "APP_"
ALIASES = {"num_workers": "workers"}
TRUE = {"true", "1", "yes", "on"}

DEFAULTS = {"port": 8000, "workers": 1, "debug": False,
            "log_level": "info", "api_key": "default-secret-000"}


def norm(key: str) -> str:
    """APP_LOG_LEVEL / log_level / NUM_WORKERS -> canonical lowercase key."""
    key = key.strip().lower()
    if key.startswith(PREFIX.lower()):
        key = key[len(PREFIX):]
    return ALIASES.get(key, key)


def yaml_layer(env: str) -> dict:
    path = ROOT / f"config.{env}.yaml"
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {norm(k): v for k, v in data.items()}


def dotenv_layer() -> dict:
    path = ROOT / ".env"
    out = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.removeprefix("export ").strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        out[norm(key)] = value
    return out


def os_layer() -> dict:
    return {norm(k): v for k, v in os.environ.items() if k.startswith(PREFIX)}


def cli_layer(pairs: list[str]) -> dict:
    out = {}
    for item in pairs:
        if "=" in item:
            key, value = item.split("=", 1)
            out[norm(key)] = value
    return out


def coerce(cfg: dict) -> dict:
    out = {}
    for key, value in cfg.items():
        if key in ("port", "workers"):
            out[key] = int(str(value).strip())
        elif key == "debug":
            out[key] = value if isinstance(value, bool) else str(value).strip().lower() in TRUE
        else:
            out[key] = str(value)
    return out


@app.get("/effective-config")
def effective_config(request: Request):
    env = os.environ.get("APP_ENV", "development")   # picks config.<env>.yaml
    cfg = dict(DEFAULTS)
    cfg.update(yaml_layer(env))
    cfg.update(dotenv_layer())
    cfg.update(os_layer())
    cfg.update(cli_layer(request.query_params.getlist("set")))   # highest precedence
    cfg.pop("env", None)                                         # APP_ENV only selects the file
    cfg = coerce(cfg)
    cfg["api_key"] = "****"                                      # never expose the secret
    return cfg
