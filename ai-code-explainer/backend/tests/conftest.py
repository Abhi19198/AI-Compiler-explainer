import os
import sys
from pathlib import Path

# Tests import the app as top-level modules (``import main``,
# ``from routers.explain import ...``), which is how uvicorn runs it from
# backend/. Make that work no matter where pytest is invoked from.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# The app must import and serve without an API key (the Anthropic client is
# lazy); make sure a stray key from the developer's shell cannot mask that.
os.environ.pop("ANTHROPIC_API_KEY", None)
