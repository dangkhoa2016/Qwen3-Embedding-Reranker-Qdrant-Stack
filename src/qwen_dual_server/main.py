from .api import create_app
from .config import Settings
from .runtime import DualModelRuntime

settings = Settings()
runtime = DualModelRuntime(settings)
app = create_app(settings, runtime)
