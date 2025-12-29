# Deployment Phases

Note: A reproducible template + rendering tool is available at templates/servarr-sso/ — see templates/servarr-sso/README-templates.md

## Phase 0: Clean Start
Suggested PR body (copy to gh or web PR description)

Title: Add reproducible Servarr SSO deployment template
Body:
What: Adds templates/servarr-sso containing .env.example, deploy.sh (renderer), caddy templates, quadlet templates, run-containers template and optional UI generator.
Why: make deployments reproducible (image pinning via .env), avoid relative-path issues with systemd user quadlets, and provide both quick-run (podman) and systemd/quadlet installation paths.
How to test: clone repo, checkout branch, run: cp templates/servarr-sso/.env.example templates/servarr-sso/.env edit .env (set BASE_PATH and image tags) cd templates/servarr-sso ./deploy.sh render sh generated/run-containers.sh # or ./deploy.sh install-quadlets (confirm)
Safety: install-quadlets prompts before copying and will not auto-enable services.
