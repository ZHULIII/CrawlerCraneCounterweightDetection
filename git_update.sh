#!/bin/bash
git add .
git commit -m "update: $(date '+%Y-%m-%d %H:%M:%S')"
git pull --rebase origin dev
git push origin dev
