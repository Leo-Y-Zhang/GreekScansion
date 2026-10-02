"""Entry point for `python -m greekscan`.

The README documents that invocation, so it needs to exist - without this file
`python -m greekscan` fails with "No module named greekscan.__main__", which is
exactly how CI caught it.
"""

from .cli import main

raise SystemExit(main())
