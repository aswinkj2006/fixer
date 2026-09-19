#!/usr/bin/env bash
# fixer.ai — One-click setup & verification script for Linux / macOS
set -e

echo "======================================================================"
echo "  fixer.ai — Setting up environment and verifying dependencies"
echo "======================================================================"

python3 scripts/bootstrap.py
