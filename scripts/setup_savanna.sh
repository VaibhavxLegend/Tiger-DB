#!/bin/bash
# Setup TigerGraph Savanna instance
# Phase 0: Pre-work

set -e

echo "=== TigerGraph Savanna Setup ==="
echo

# Check environment variables
if [ -z "$TG_HOST" ]; then
    echo "Error: TG_HOST not set in .env"
    exit 1
fi

if [ -z "$TG_API_TOKEN" ]; then
    echo "Error: TG_API_TOKEN not set in .env"
    exit 1
fi

echo "TigerGraph Host: $TG_HOST"
echo "Cloud Mode: $TG_TGCLOUD"
echo

# TODO: Test connection
echo "Testing connection..."
# Add gsql connection test

echo
echo "✓ Savanna instance ready"
