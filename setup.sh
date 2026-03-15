#!/usr/bin/bash

for f in ./controller/*.py; do
    chmod +x "$f"
done
