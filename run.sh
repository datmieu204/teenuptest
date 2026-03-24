#!/usr/bin/env bash
set -e

COMMAND=${1:-up}

if [[ "$COMMAND" == "up" ]]; then
  docker compose up --build
elif [[ "$COMMAND" == "down" ]]; then
  docker compose down
elif [[ "$COMMAND" == "reset" ]]; then
  docker compose down -v
else
  echo "Usage: ./run.sh [up|down|reset]"
  exit 1
fi
