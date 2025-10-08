from __future__ import annotations
import shlex, subprocess

def run(cmd: str):
    p = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p.returncode, p.stdout.decode('utf-8', 'ignore'), p.stderr.decode('utf-8', 'ignore')
