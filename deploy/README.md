Maze Forest — Remote Server Deployment

You have three solid ways to serve this static HTML5/Canvas game from a remote machine. Pick the one that matches your setup and appetite for polish.

Option A — Fastest: Docker + Nginx (recommended)
- Works on any box with Docker; zero host config leakage; easy to update.

1) Prereqs on the server
   - Install Docker + Compose plugin (Ubuntu):
     - sudo apt-get update
     - sudo apt-get install -y ca-certificates curl gnupg
     - sudo install -m 0755 -d /etc/apt/keyrings
     - curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
     - echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
     - sudo apt-get update && sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
   - Optional: add your user to the docker group, then re-login:
     - sudo usermod -aG docker $USER

2) Copy the project to the server (keeping this repo structure):
   - maze-forest/
   - deploy/

3) On the server, from the deploy/ folder:
   - docker compose up -d
   - Visit http://YOUR_SERVER_IP/ (port 80). If a firewall is on, allow 80/tcp.

4) HTTPS (optional but recommended)
   - Easiest: put this behind a reverse proxy like Caddy or Traefik with automatic TLS, or run an nginx-proxy + letsencrypt companion. If you prefer bare-metal Nginx + Certbot, see Option C.

Update cycle
- Pull/rsync new files into maze-forest/, then: docker compose restart


Option B — Quick-and-dirty: Python HTTP server (good for testing)
- One command, minimal moving parts. Not for production.

1) On the server:
   - sudo ufw allow 8000/tcp   # if UFW is enabled
   - cd /path/to/maze-forest
   - python3 -m http.server 8000 --bind 0.0.0.0
   - Browse: http://YOUR_SERVER_IP:8000/

2) Keep it running (optional)
   - nohup python3 -m http.server 8000 --bind 0.0.0.0 >/var/log/maze-forest.http.log 2>&1 &
   - Or create a systemd unit (left out here to avoid clutter).


Option C — Bare-metal Nginx (production-friendly)
- Serve the static files directly with Nginx; easy, fast, low memory.

1) Install and open firewall (Ubuntu/Debian)
   - sudo apt-get update && sudo apt-get install -y nginx
   - sudo ufw allow 'Nginx Full'  # opens ports 80 and 443

2) Place files and enable site
   - sudo mkdir -p /var/www/maze-forest
   - sudo rsync -av --delete ./maze-forest/ /var/www/maze-forest/
   - sudo cp ./deploy/nginx-site.conf /etc/nginx/sites-available/maze-forest
   - sudo sed -i "s/example.com/YOUR_DOMAIN/g" /etc/nginx/sites-available/maze-forest
   - sudo ln -s /etc/nginx/sites-available/maze-forest /etc/nginx/sites-enabled/maze-forest || true
   - sudo nginx -t && sudo systemctl reload nginx
   - Test: http://YOUR_DOMAIN/ (or your server IP if you set server_name to the IP)

3) Enable HTTPS with Certbot
   - sudo apt-get install -y certbot python3-certbot-nginx
   - sudo certbot --nginx -d YOUR_DOMAIN -d www.YOUR_DOMAIN
   - Auto-renew is installed by Certbot; verify with: systemctl list-timers | grep certbot

4) Deploy updates
   - sudo rsync -av --delete ./maze-forest/ /var/www/maze-forest/
   - sudo systemctl reload nginx


Notes and pitfalls
- This project is purely static (HTML/CSS/JS). No server frameworks or build steps are required.
- If you see 403/404 on assets, ensure the root path is correct and permissions allow Nginx to read files (www-data on Debian/Ubuntu).
- If hosting behind another reverse proxy or load balancer, ensure it forwards to port 80 of the container/host serving the files.
- For very small VPS instances, Nginx memory footprint is minimal; Docker adds ~100MB overhead but simplifies ops.

Troubleshooting quick checks
- curl -I http://localhost/ on the server should show HTTP/1.1 200 OK
- docker logs $(docker ps -qf name=maze) if using Docker
- sudo nginx -t for config syntax; tail -f /var/log/nginx/error.log for runtime issues

