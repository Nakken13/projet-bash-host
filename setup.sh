#!/usr/bin/bash

for f in ./controller/*.py; do
    chmod +x "$f"
    echo "chmod +x $f"
done
