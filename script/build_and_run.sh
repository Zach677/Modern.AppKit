#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-run}"
APP_NAME="ModernAppKit"
CONFIGURATION="${CONFIGURATION:-Debug}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

usage() {
    echo "usage: $0 [run|--debug|--logs|--telemetry|--verify]" >&2
}

if [ "$#" -gt 1 ]; then
    usage
    exit 2
fi

case "$MODE" in
    run | --debug | debug | --logs | logs | --telemetry | telemetry | --verify | verify) ;;
    *)
        usage
        exit 2
        ;;
esac

case "$CONFIGURATION" in
    debug | Debug) CONFIGURATION="Debug" ;;
    release | Release) CONFIGURATION="Release" ;;
    *)
        echo "Unsupported CONFIGURATION: $CONFIGURATION" >&2
        exit 64
        ;;
esac

DERIVED_DATA="${DERIVED_DATA:-$ROOT_DIR/.DerivedData}"
case "$DERIVED_DATA" in
    /*) ;;
    *) DERIVED_DATA="$ROOT_DIR/$DERIVED_DATA" ;;
esac
mkdir -p "$DERIVED_DATA"
DERIVED_DATA="$(cd "$DERIVED_DATA" && pwd -P)"

APP_BUNDLE="$DERIVED_DATA/Build/Products/$CONFIGURATION/$APP_NAME.app"
APP_BINARY="$APP_BUNDLE/Contents/MacOS/$APP_NAME"

cd "$ROOT_DIR"

process_matches_app_binary() {
    /usr/sbin/lsof -a -p "$1" -d txt -Fn 2>/dev/null | grep -Fqx "n$APP_BINARY"
}

stop_running_app() {
    local pid
    while IFS= read -r pid; do
        [ -n "$pid" ] || continue
        if process_matches_app_binary "$pid"; then
            kill "$pid"
        fi
    done < <(pgrep -x "$APP_NAME" || true)
}

app_is_running() {
    local pid
    while IFS= read -r pid; do
        [ -n "$pid" ] || continue
        if process_matches_app_binary "$pid"; then
            return 0
        fi
    done < <(pgrep -x "$APP_NAME" || true)
    return 1
}

stop_running_app
mise run build-macos -- CONFIGURATION="$CONFIGURATION"
test -d "$APP_BUNDLE"
BUNDLE_ID="$(/usr/libexec/PlistBuddy -c "Print :CFBundleIdentifier" "$APP_BUNDLE/Contents/Info.plist")"

open_app() {
    /usr/bin/open -n "$APP_BUNDLE"
}

case "$MODE" in
    run)
        open_app
        ;;
    --debug | debug)
        lldb -- "$APP_BINARY"
        ;;
    --logs | logs)
        open_app
        /usr/bin/log stream --info --style compact --predicate "process == \"$APP_NAME\""
        ;;
    --telemetry | telemetry)
        open_app
        /usr/bin/log stream --info --style compact --predicate "subsystem == \"$BUNDLE_ID\""
        ;;
    --verify | verify)
        open_app
        for _ in {1..100}; do
            if app_is_running; then
                exit 0
            fi
            sleep 0.1
        done
        echo "$APP_NAME did not launch" >&2
        exit 1
        ;;
esac
