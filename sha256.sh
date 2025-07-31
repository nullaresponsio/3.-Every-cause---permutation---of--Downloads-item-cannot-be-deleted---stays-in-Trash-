#!/usr/bin/env bash

# Compute SHA-256 checksum of a file on macOS

if [[ -z "$1" ]]; then
  echo "Usage: $0 <file>"
  exit 1
fi

shasum -a 256 "$1"
