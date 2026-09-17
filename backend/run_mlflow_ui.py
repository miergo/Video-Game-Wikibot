"""Start the MLflow tracking server with a local file store.

Traces and metrics are persisted under ./mlruns/ by default.

Usage:
    python run_mlflow_ui.py            # default port 5000
    python run_mlflow_ui.py 5001       # custom port
"""

from __future__ import annotations

import subprocess
import sys


def main() -> None:
    port = sys.argv[1] if len(sys.argv) > 1 else "5000"
    print(f"Starting MLflow UI on http://localhost:{port} ...")
    raise SystemExit(
        subprocess.call(
            [
                sys.executable,
                "-m",
                "mlflow",
                "server",
                "--host",
                "0.0.0.0",
                "--port",
                port,
            ]
        )
    )


if __name__ == "__main__":
    main()
