# Truckmodell Vorarlberg — Website

Moderner Neubau der Website des Vereins **Truckmodell Vorarlberg**
([truckmodell.at](https://truckmodell.at)) — Truck- und Funktionsmodellbau
im Maßstab 1:12 bis 1:16.

> **Live (Entwurf):** https://tmv.teraware.net
> **Status:** Statischer Design-Prototyp. Der spätere Ausbau zur vollen
> Next.js-App mit Admin/CMS nutzt dasselbe Deploy-Muster.

---

## Inhalt

- [Überblick](#überblick)
- [Design](#design)
- [Repo-Struktur](#repo-struktur)
- [Prototyp bauen](#prototyp-bauen-aus-src)
- [Deployment & Infrastruktur](#deployment--infrastruktur)
- [Auto-Deploy (Autoinstall)](#auto-deploy-autoinstall)
- [Update-Workflow](#update-workflow)
- [Server-Betrieb (Cheat-Sheet)](#server-betrieb-cheat-sheet)
- [Roadmap](#roadmap)
- [Vereinsdaten](#vereinsdaten)

---

## Überblick

Die aktuelle Seite ist eine einzige, **in sich geschlossene** `public/index.html`
(rund 5,5 MB) — alle Fotos und Schriften sind als `data:`-URIs eingebettet.
Dadurch läuft die Seite **komplett offline** und lässt sich als einzelne Datei
weitergeben.

**Seiten / Funktionen**

| Bereich | Inhalt |
|---|---|
| Start | Foto-Hero, Vereins-Story, Vorstand, Kennzahlen |
| Modelle | 115 echte Modelle mit Foto + Besitzer, Live-Suche & Kategorie-Filter, Detail-Modal |
| Parcours | Zeitleiste (2012–2024), Inventar, Foto-Galerie |
| Beiträge | News-Karten (Beispielinhalte – später aus CMS) |
| Termine | Messen/Events (Tulln, Faszination Modellbau) |
| Kontakt | 3 Tab-Formulare (Gastfahrer / Allgemein / Obmann) |
| Impressum & Datenschutz | echte Vereinsdaten |

Technisch: Hell/Dunkel-Umschalter, Hash-Routing (Single-Page), Scroll-Reveals,
voll responsive (Desktop / Tablet / Handy), ohne externe Abhängigkeiten
(CSP-fest, kein CDN).

## Design

- **Richtung:** hell & foto-zentriert, warmes Off-White, viel Weißraum.
- **Akzentfarbe:** Rot `#C4161C` — aus dem echten Vereinslogo abgeleitet, dezent eingesetzt.
- **Typografie:** *Bricolage Grotesque* (Display) + *Instrument Sans* (Text),
  als woff2 eingebettet (kein Font-CDN nötig).
- **Fotos:** echte Modell-/Parcoursbilder von truckmodell.at, mit Python/Pillow
  optimiert (max. 500 px, JPEG q66) und eingebettet.

## Repo-Struktur

```
public/index.html          Ausgelieferte Seite (self-contained, aus src/ gebaut)
src/
  tmv2.src.html            Markup/CSS/JS mit Platzhaltern /*__FONTS__*/ /*__ASSETS__*/
  _fonts2.css              @font-face mit eingebetteten woff2 (data-URI)
  assets.js                window.TMV_ASSETS = { logo, hero, parcours, props, models[] }
  build_assets.py          lädt & optimiert die Fotos -> assets.js (Pillow)
Dockerfile                 nginx:alpine, serviert public/ (gzip)
nginx.conf                 Server-Block (gzip, SPA-Fallback)
docker-compose.yml         web + cloudflared (Tunnel) + webhook (Auto-Deploy)
deploy/
  webhook.js               HMAC-verifizierter GitHub-Webhook -> deploy.sh
  deploy.sh                git pull + docker compose up -d --build web
  Dockerfile               node:alpine + docker-cli für den Webhook
cloudflared/
  config.yml.example       Tunnel-Ingress (tmv / tmv-hook . teraware.net)
.env.example               WEBHOOK_SECRET
VERSION
```

`.env`, `cloudflared/config.yml` und `cloudflared/creds.json` sind
**servergebunden** und per `.gitignore` ausgeschlossen (keine Secrets im Repo).

## Prototyp bauen (aus `src/`)

Die ausgelieferte `public/index.html` wird aus den Quellen zusammengesetzt —
die Fonts und die Foto-Assets werden in die Marker eingefügt:

```bash
# Fotos (neu) optimieren und einbetten -> src/assets.js
python src/build_assets.py

# Fonts + Assets in die Platzhalter einsetzen -> public/index.html
awk '/\/\*__FONTS__\*\//{while((getline l < "src/_fonts2.css")>0)print l;next}
     /\/\*__ASSETS__\*\//{while((getline l < "src/assets.js")>0)print l;next}
     {print}' src/tmv2.src.html > public/index.html
```

## Deployment & Infrastruktur

Läuft auf dem TeraWare-Entwicklungsserver **`192.168.5.15`** unter `/opt/tmv`,
öffentlich über einen **eigenen Cloudflare Tunnel** (kein offener Port, kein
Eingriff in den geteilten teraware.net-Tunnel). Drei Container:

| Container | Aufgabe |
|---|---|
| `tmv-web` | nginx, serviert `public/index.html` |
| `tmv-tunnel` | Cloudflare Tunnel → `tmv.teraware.net` |
| `tmv-webhook` | GitHub-Webhook für Auto-Deploy (`tmv-hook.teraware.net`) |

```bash
cd /opt/tmv
cp .env.example .env            # WEBHOOK_SECRET setzen
# cloudflared/config.yml aus .example mit echter Tunnel-UUID erzeugen,
# cloudflared/creds.json = /root/.cloudflared/<UUID>.json
docker compose up -d --build
```

**Tunnel & DNS** (einmalig, mit vorhandenem `cert.pem`):

```bash
cloudflared tunnel create tmv
cloudflared tunnel route dns tmv tmv.teraware.net
cloudflared tunnel route dns tmv tmv-hook.teraware.net
```

## Auto-Deploy (Autoinstall)

Push auf `main` → GitHub-Webhook → `https://tmv-hook.teraware.net/webhook`
→ `deploy/webhook.js` prüft die HMAC-Signatur (`WEBHOOK_SECRET`) und startet
`deploy/deploy.sh`:

```
git pull origin main  →  docker compose up -d --build web  →  image prune
```

Sicherheit des Webhooks: nur über den Tunnel erreichbar, **HMAC-SHA256**-signiert,
startet nur mit gesetztem Secret (fail-closed), Body-Limit + Timeout gegen DoS.
Der Docker-Socket-Mount ist bewusst gesetzt (nötig, um `docker compose` beim
Deploy auszuführen).

## Update-Workflow

```bash
# 1) lokal ändern (Design in src/, dann public/index.html neu bauen – siehe oben)
# 2) committen & pushen
git add -A && git commit -m "…" && git push origin main
# 3) fertig – der Server deployt automatisch (Webhook). Kein SSH nötig.
```

## Server-Betrieb (Cheat-Sheet)

```bash
ssh root@192.168.5.15
cd /opt/tmv
docker compose ps
docker compose logs -f web         # nginx
docker logs -f tmv-webhook         # Auto-Deploy-Log
docker logs -f tmv-tunnel          # Tunnel-Status
docker compose up -d --build       # manuell neu bauen (alle Services)
```

## Roadmap

Der statische Prototyp wird durch die vollständige **Next.js-App mit Admin/CMS**
ersetzt (Modelle, News und Termine pflegbar; Login; SQLite) — gleiches
Deploy-Muster (Container + Tunnel + Webhook), gleiche Domain.

## Vereinsdaten

- **Verein:** Truckmodell Vorarlberg · ZVR 913632854
- **Sitz:** Gardis 24, 6811 Göfis, Österreich
- **Obmann:** Klaus Waibel · **Stv.:** Peter Erich
- **Kontakt:** info@truckmodell.at
- **Social:** facebook / instagram / youtube — `@truckmodellvorarlberg`
- **Gegründet:** 2011 (Verein seit 2015) · **Maßstab:** 1:12–1:16

---

*Neubau-Entwurf · TeraWare-OG/tmv · Deployment: Cloudflare Tunnel + Auto-Deploy*
