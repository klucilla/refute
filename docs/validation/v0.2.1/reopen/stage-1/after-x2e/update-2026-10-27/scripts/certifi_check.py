"""Which CA bundle the running environment uses (dependencies-reachability.md: downloads resume only
when the environment that runs them uses the corrected bundle). No network.
certifi_check.py <out.json>"""

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import certifi
import requests
import requests.certs

where = Path(requests.certs.where()).resolve()
Path(sys.argv[1]).write_text(
    json.dumps(
        {
            "checked_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            "python": sys.executable,
            "certifi_version": certifi.__version__,
            "requests_version": requests.__version__,
            "requests_certs_where": where.as_posix(),
            "certifi_where": Path(certifi.where()).resolve().as_posix(),
            "same_bundle": where == Path(certifi.where()).resolve(),
            "bundle_sha256": hashlib.sha256(where.read_bytes()).hexdigest(),
        },
        indent=1,
    )
    + "\n",
    encoding="utf-8",
    newline="\n",
)
print(Path(sys.argv[1]).read_text(encoding="utf-8"))
