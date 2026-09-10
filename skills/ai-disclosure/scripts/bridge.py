"""Private stdin JSON bridge for the optional Node publishing client."""
import json
from pathlib import Path
import runpy
import sys


def main():
    try:
        raw = sys.stdin.buffer.read(32 * 1024 * 1024 + 1)
        if len(raw) > 32 * 1024 * 1024:
            raise ValueError("Request exceeds 32 MiB")
        request = json.loads(raw)
        allowed = {"command", "root", "html", "manifest", "page", "title", "language"}
        if not isinstance(request, dict) or set(request) - allowed:
            raise ValueError("Expected a publishing request with supported fields")
        command = request.get("command")
        if command not in {"inspect", "render", "export"}:
            raise ValueError("Unsupported publishing command")
        if not isinstance(request.get("root"), str) or not Path(request["root"]).is_absolute():
            raise ValueError("root must be an absolute public asset directory")
        root = Path(request["root"])
        if not root.is_dir():
            raise ValueError("Public asset directory does not exist")
        if not isinstance(request.get("html"), str) or not isinstance(request.get("page", "index.html"), str):
            raise ValueError("html and page must be strings")
        publisher = runpy.run_path(str(Path(__file__).with_name("site.py")))
        args = (root, request["html"])
        page = request.get("page", "index.html")
        if command == "inspect":
            result = publisher["fragment_inventory"](*args, page)[1]
            code = int(bool(result["gaps"]))
        elif command == "render":
            result = publisher["render_fragment"](*args, request.get("manifest"), page)
            code = int(result["html"] is None)
        else:
            result = publisher["export_document"](*args, request.get("manifest"),
                                                   request.get("title"), request.get("language"), page)
            code = int(result["html"] is None)
        print(json.dumps(result))
        return code
    except (ValueError, OSError, TypeError) as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
