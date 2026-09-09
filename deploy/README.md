# Deployment configuration

This folder contains the server-side configuration for `renovation.posifit.eu`,
captured from the production server so the site can be redeployed on a new
server without having to reconstruct these files from memory.

## Contents

- `nginx/renovation.posifit.eu.conf` — the Nginx server block (reverse proxy to
  the Flask app on `127.0.0.1:8050` and the Dash app on `127.0.0.1:8051`,
  static file serving, security headers, gzip).
- `supervisor/legofit.conf` — Supervisor program definitions that keep the
  Flask (`main:server`) and Dash (`wsgi:server`) Gunicorn processes running.

## Restoring on a new server

1. Install system packages: `nginx`, `supervisor`, `python3-venv`, `certbot`
   (`python3-certbot-nginx`).
2. Clone this repo to `/var/www/legofit-explorer.com` (path referenced by the
   configs below; rename consistently if you use a different path).
3. Create the virtualenv and install dependencies:
   ```bash
   cd /var/www/legofit-explorer.com
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
4. Copy the Nginx config and enable the site:
   ```bash
   cp deploy/nginx/renovation.posifit.eu.conf /etc/nginx/sites-available/renovation.posifit.eu
   ln -s /etc/nginx/sites-available/renovation.posifit.eu /etc/nginx/sites-enabled/
   ```
5. Get/renew the SSL certificate (the old cert/key are NOT in this repo, they
   never should be — Certbot will issue fresh ones):
   ```bash
   certbot --nginx -d renovation.posifit.eu -d www.renovation.posifit.eu
   ```
6. Copy the Supervisor config:
   ```bash
   cp deploy/supervisor/legofit.conf /etc/supervisor/conf.d/legofit.conf
   supervisorctl reread && supervisorctl update
   supervisorctl restart legofit:*
   ```
7. Point the domain's DNS `A`/`AAAA` record at the new server's IP.
8. Test with `nginx -t`, then `systemctl reload nginx`.

## Notes

- `data/` (Excel data files) and `assets/`/`static/` (images, JS/CSS) are
  included in the repo since the app depends on them at runtime.
- `venv/`, `__pycache__/`, `.DS_Store`, log files and old timestamped
  `*.backup.*` files are excluded via `.gitignore` — they're either
  regenerable or not needed.
