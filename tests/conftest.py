import sys
from pathlib import Path

# Permite `import benchmark_runner` al correr pytest desde cualquier cwd.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
