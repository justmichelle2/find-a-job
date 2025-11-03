#!/usr/bin/env python
"""Proxy manage.py for the jobboard folder.

This forwards execution to the project's root manage.py so you can run
`py manage.py ...` from inside `jobboard`.
"""
import os
import sys

here = os.path.dirname(__file__)
root = os.path.abspath(os.path.join(here, '..'))
manage_py = os.path.join(root, 'manage.py')

if not os.path.exists(manage_py):
    sys.stderr.write("Error: manage.py not found in project root ({})\n".format(root))
    sys.exit(2)

# Replace current process with the real manage.py using the same Python executable
os.execv(sys.executable, [sys.executable, manage_py] + sys.argv[1:])
