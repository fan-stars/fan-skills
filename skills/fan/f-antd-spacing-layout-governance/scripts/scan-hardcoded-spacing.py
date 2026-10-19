#!/usr/bin/env python3
import sys

from scan_spacing import main

raise SystemExit(main(["--checks", "hardcode,inline-style,custom-token", *sys.argv[1:]]))
