# Licences of the engine-trial tools (v0.5.10, part (f)), read 2026-11-24

Recorded before any run, as the v0.5.10 charter, part (f), asks; the rule of issue #34: URL,
retrieval date and a short literal excerpt. Read on 2026-11-24 at about 15:55Z, from each
repository's default branch (`HEAD`), and from PyPI's metadata of the pinned version. The licence
of the pinned version's own distribution is the one declared in its PyPI metadata; where the
repository file and PyPI agree, both are given.

| Tool (pinned) | Licence | Source and excerpt |
|---|---|---|
| exovetter 0.0.16 | BSD 3-Clause | https://raw.githubusercontent.com/spacetelescope/exovetter/HEAD/LICENSE.rst: "Copyright 2020 Space Telescope Science Institue" and "Redistribution and use in source and binary forms, with or without"; PyPI metadata `license`: "BSD 3-Clause" (https://pypi.org/pypi/exovetter/0.0.16/json) |
| triceratops 1.1.0 | MIT | https://raw.githubusercontent.com/stevengiacalone/triceratops/HEAD/LICENSE: "The MIT License (MIT)" and "Copyright (c) 2020 stevengiacalone"; PyPI classifier "License :: OSI Approved :: MIT License" |
| wotan 2.1 | MIT | https://raw.githubusercontent.com/hippke/wotan/HEAD/LICENSE: "MIT License" and "Copyright (c) 2019 Michael Hippke"; PyPI metadata `license`: "MIT" |
| transitleastsquares 2.3.0 | MIT | https://raw.githubusercontent.com/hippke/tls/HEAD/LICENSE: "MIT License" and "Copyright (c) 2018 Michael Hippke"; PyPI `license_expression`: "MIT" |
| leo-vetter 1.2.0 | GPL-3.0 or later | https://raw.githubusercontent.com/mkunimoto/LEO-Vetter/HEAD/LICENSE: "GNU GENERAL PUBLIC LICENSE" and "Version 3, 29 June 2007"; PyPI classifier "GNU General Public License v3 or later (GPLv3+)" |

**GPL code among the resolved dependencies** (PyPI metadata of the pinned versions, read
2026-11-24):
- pytransit 2.2.0 (a dependency of triceratops): "GPLv2"; classifier "GNU General Public License
  v2 (GPLv2)". Repository file:
  https://raw.githubusercontent.com/hpparvi/PyTransit/HEAD/LICENSE: "GNU GENERAL PUBLIC LICENSE"
  and "Version 2, June 1991".
- batman-package 2.5.3 (a dependency of leo-vetter): PyPI metadata `license`: "GNU GPLv3". The
  repository's licence file was not found at `LICENSE` or `COPYING` on 2026-11-24: **the
  repository's own statement is not confirmed**; the PyPI metadata is.

The licence of every one of the 119 resolved packages, as declared in its PyPI metadata, is in
[docs/validation/v0.5.10/engines/licences.json](../validation/v0.5.10/engines/licences.json).
Metadata is a declaration by the publisher, not a legal review: any licence that matters for
incorporation into Refute's code is checked again, from the distributed files, in the
version-5 phase.
