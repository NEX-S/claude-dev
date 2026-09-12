#!/bin/sh
set -eu

SRC=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec bun "$SRC/scripts/install.ts" "$@"
