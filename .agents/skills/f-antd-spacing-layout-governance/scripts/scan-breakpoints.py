#!/usr/bin/env python3
import sys

from scan_spacing import main

raise SystemExit(main(["--checks", "breakpoint", *sys.argv[1:]]))
