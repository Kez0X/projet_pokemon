"""Point d'entrée pour Vercel : Vercel cherche une application Flask nommée `app`.
Dash tourne sur un serveur Flask, qu'on expose ici."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dashboard import server as app  # noqa: E402,F401
