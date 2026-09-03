from pathlib import Path

from fastapi.templating import Jinja2Templates

PROJECT_ROOT = Path(__file__).resolve().parents[4]
templates = Jinja2Templates(directory=PROJECT_ROOT / "frontend" / "src" / "views")
