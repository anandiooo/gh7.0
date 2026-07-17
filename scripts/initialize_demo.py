import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main() -> int:
    from src.config import DB_PATH
    from src.enums import WorkspaceMode
    from src.errors import TetaniError
    from src.services.workspace_service import initialize_workspace, read_workspace_counts

    try:
        initialize_workspace(WorkspaceMode.DEMO, DB_PATH)
        counts = read_workspace_counts(DB_PATH)
    except TetaniError as error:
        print(f"Demo initialization failed: {error}", file=sys.stderr)
        return 1
    except Exception:
        print("Demo initialization failed unexpectedly.", file=sys.stderr)
        return 1
    summary = ", ".join(f"{key}={value}" for key, value in counts.as_dict().items())
    print(f"Demo workspace initialized: {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
