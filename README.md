# Truckmodell Vorarlberg — Website (Prototyp)

Moderner Neubau-Entwurf der Vereinswebsite von **Truckmodell Vorarlberg**
(truckmodell.at). Aktuell ein **statischer Design-Prototyp** — eine einzige,
self-contained `public/index.html` mit eingebetteten Fotos und Schriften.

**Live:** https://tmv.uebelher.biz

## Stack / Deployment

Läuft auf dem Server `192.168.5.107` unter `/opt/tmv`, öffentlich erreichbar über
einen **Cloudflare Tunnel** (kein offener Port). Drei Container:

- `tmv-web` — nginx, serviert `public/index.html`
- `tmv-tunnel` — Cloudflare Tunnel → `tmv.uebelher.biz`
- `tmv-webhook` — GitHub-Webhook für Auto-Deploy bei Push auf `main`

```bash
cd /opt/tmv
cp .env.example .env          # WEBHOOK_SECRET eintragen
docker compose up -d --build
```

**DNS:** `cloudflared tunnel route dns tmv tmv.uebelher.biz`
(+ `tmv-hook.uebelher.biz`), CNAME auf den Tunnel.

**Auto-Deploy (Autoinstall):** Push auf `main` → GitHub-Webhook →
`tmv-hook.uebelher.biz/webhook` → `deploy/deploy.sh` macht `git pull` +
`docker compose up -d --build web`.

## Prototyp bauen

Die ausgelieferte `public/index.html` wird aus den Quellen in `src/` erzeugt:

- `src/tmv2.src.html` — Markup/CSS/JS (mit Platzhaltern `/*__FONTS__*/`, `/*__ASSETS__*/`)
- `src/_fonts2.css` — eingebettete Web-Fonts (Bricolage Grotesque, Instrument Sans) als data-URI
- `src/assets.js` — `window.TMV_ASSETS` mit allen Fotos (data-URI), erzeugt von `src/build_assets.py`

Zusammenbau (Fonts + Assets in die Marker einsetzen):

```bash
awk '/\/\*__FONTS__\*\//{while((getline l < "src/_fonts2.css")>0)print l;next}
     /\/\*__ASSETS__\*\//{while((getline l < "src/assets.js")>0)print l;next}
     {print}' src/tmv2.src.html > public/index.html
```

## Roadmap

Der statische Prototyp wird später durch die vollständige **Next.js-App mit
Admin/CMS** (Modelle, News, Termine pflegbar) ersetzt — gleiches Deploy-Muster.
