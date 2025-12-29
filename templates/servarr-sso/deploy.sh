#!/bin/sh
# deploy.sh - render and optionally install templates
# Usage:
#   ./deploy.sh render    # renders templates into generated/
#   ./deploy.sh install-quadlets  # copies rendered quadlets into ~/.config/containers/systemd/ (prompts)
set -eu

TEMPLATE_DIR="$(cd "$(dirname "$0")" && pwd)"
GENERATED_DIR="$TEMPLATE_DIR/generated"
USER_QUADLET_DIR="${HOME}/.config/containers/systemd"

load_env() {
  if [ -f "$TEMPLATE_DIR/.env" ]; then
    # shellcheck disable=SC1090
    set -a
    . "$TEMPLATE_DIR/.env"
    set +a
  else
    echo ".env not found in $TEMPLATE_DIR. Please copy .env.example -> .env and edit it."
    exit 1
  fi
}

# fallback BASE_PATH to current dir if empty
ensure_base_path() {
  if [ -z "${BASE_PATH:-}" ] || [ "$BASE_PATH" = "__ABSOLUTE_BASE_PATH__" ]; then
    BASE_PATH="$(pwd)"
    echo "BASE_PATH not set; falling back to current directory: $BASE_PATH"
  fi
}

render_file() {
  src="$1"
  dst="$2"
  mkdir -p "$(dirname "$dst")"
  sed \
    -e "s|__BASE_PATH__|$BASE_PATH|g" \
    -e "s|__CADDY_EMAIL__|$CADDY_EMAIL|g" \
    -e "s|__OUTPOST_URI__|$OUTPOST_URI|g" \
    -e "s|__AUTHENTIK_IMAGE__|$AUTHENTIK_IMAGE|g" \
    -e "s|__CADDY_IMAGE__|$CADDY_IMAGE|g" \
    -e "s|__HOMARR_IMAGE__|$HOMARR_IMAGE|g" \
    -e "s|__JELLYFIN_IMAGE__|$JELLYFIN_IMAGE|g" \
    -e "s|__NAVIDROME_IMAGE__|$NAVIDROME_IMAGE|g" \
    -e "s|__AUDIOBOOKSHELF_IMAGE__|$AUDIOBOOKSHELF_IMAGE|g" \
    -e "s|__KAVITA_IMAGE__|$KAVITA_IMAGE|g" \
    -e "s|__VAULTWARDEN_IMAGE__|$VAULTWARDEN_IMAGE|g" \
    -e "s|__RADARR_IMAGE__|$RADARR_IMAGE|g" \
    -e "s|__SONARR_IMAGE__|$SONARR_IMAGE|g" \
    -e "s|__LIDARR_IMAGE__|$LIDARR_IMAGE|g" \
    -e "s|__PUID__|$PUID|g" \
    -e "s|__PGID__|$PGID|g" \
    -e "s|__TZ__|$TZ|g" \
    "$src" > "$dst"
  chmod --reference="$src" "$dst" 2>/dev/null || true
}

render_all() {
  echo "Rendering templates from $TEMPLATE_DIR -> $GENERATED_DIR"
  rm -rf "$GENERATED_DIR"
  mkdir -p "$GENERATED_DIR"
  find "$TEMPLATE_DIR" -type f | while IFS= read -r f; do
    case "$f" in
      */generated/*) continue ;;
      */deploy.sh) continue ;;
      */.env.example) continue ;;
    esac
    rel="${f#$TEMPLATE_DIR/}"
    dst="$GENERATED_DIR/$rel"
    render_file "$f" "$dst"
  done
  echo "Rendered files are in $GENERATED_DIR"
  echo "Run: less $GENERATED_DIR/run-containers.sh to inspect podman run commands."
  echo "To install quadlets: ./deploy.sh install-quadlets"
}

validate_env_vars() {
  missing=0
  for var in BASE_PATH CADDY_EMAIL AUTHENTIK_IMAGE CADDY_IMAGE HOMARR_IMAGE JELLYFIN_IMAGE; do
    if [ -z "${!var:-}" ]; then
      echo "Required env var $var is not set"
      missing=1
    fi
  done
  if [ "$missing" -ne 0 ]; then
    echo "One or more required environment variables are missing. Copy and edit .env from .env.example and try again."
    exit 1
  fi
}

install_quadlets() {
  echo "This will copy quadlets from $GENERATED_DIR/quadlets to $USER_QUADLET_DIR. Continue? [y/N]"
  read ans
  if [ "$ans" != "y" ] && [ "$ans" != "Y" ]; then
    echo "Aborted."
    exit 0
  fi
  mkdir -p "$USER_QUADLET_DIR"
  cp -v "$GENERATED_DIR/quadlets/"*.container "$USER_QUADLET_DIR/"
  echo "Reloading systemd --user"
  systemctl --user daemon-reload
  echo "Quadlets copied. You can enable/start services with systemctl --user enable --now <name>.service"
}

case "${1:-}" in
  render) load_env; ensure_base_path; render_all ;;
  install-quadlets) load_env; ensure_base_path; render_all; install_quadlets ;;
  *)
    echo "Usage: $0 {render|install-quadlets}"
    exit 1
    ;;
esac
