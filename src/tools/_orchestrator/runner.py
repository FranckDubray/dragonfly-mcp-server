#!/usr/bin/env python3
# Thin entrypoint to keep module size <7KB; delegates to runner_main
from .runner_main import main

if __name__ == '__main__':
    main()
