#!/usr/bin/env python3
import sys

from scan_spacing import main

raise SystemExit(main(["--checks", "gap,hardcode", *sys.argv[1:]]))
