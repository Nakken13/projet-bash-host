#!/usr/bin/bash

for f in ./controller/*.py; do
    chmod +x "$f"
done

for f in ./controller/utils/*.py; do
    chmod +x "$f"
done