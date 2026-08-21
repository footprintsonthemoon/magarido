#!/usr/bin/env python3

from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import webbrowser


HOST = "127.0.0.1"
PORT = 8080

RESULTS_DIR = Path("tests/results")
INDEX_FILE = RESULTS_DIR / "index.html"


def create_index():
    maps = sorted(RESULTS_DIR.glob("*/comparison.html"))

    links = []

    for comparison in maps:
        route_name = comparison.parent.name

        display_name = (
            route_name
            .replace("-", " ")
            .title()
        )

        relative_path = comparison.relative_to(RESULTS_DIR)

        links.append(
            f"""
            <a class="route" href="{relative_path}">
                {display_name}
            </a>
            """
        )

    document = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta
    name="viewport"
    content="width=device-width, initial-scale=1"
>
<title>BRouter Calibration Results</title>

<style>
body {{
    max-width: 800px;
    margin: 50px auto;
    padding: 0 20px;

    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;

    background: #f7f7f8;
}}

h1 {{
    margin-bottom: 5px;
}}

p {{
    color: #555;
    margin-bottom: 30px;
}}

.routes {{
    display: grid;
    gap: 12px;
}}

.route {{
    display: block;

    padding: 18px 20px;

    background: white;
    border: 1px solid #ddd;
    border-radius: 8px;

    color: #111;
    text-decoration: none;

    font-size: 17px;
}}

.route:hover {{
    background: #f0f0f0;
}}
</style>
</head>

<body>

<h1>BRouter Motorcycle Calibration</h1>

<p>
Select a calibration route to compare the motorcycle profiles.
</p>

<div class="routes">
{''.join(links)}
</div>

</body>
</html>
"""

    INDEX_FILE.write_text(
        document,
        encoding="utf-8",
    )


def main():
    if not RESULTS_DIR.exists():
        raise SystemExit(
            "tests/results does not exist. "
            "Run tools/run_calibration_tests.py first."
        )

    create_index()

    url = (
        f"http://{HOST}:{PORT}/"
        "tests/results/index.html"
    )

    print()
    print("BRouter calibration results")
    print("---------------------------")
    print(url)
    print()
    print("Press Ctrl-C to stop.")
    print()

    server = ThreadingHTTPServer(
        (HOST, PORT),
        SimpleHTTPRequestHandler,
    )

    webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
