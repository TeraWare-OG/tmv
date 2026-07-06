FROM nginx:alpine

# eigene Server-Config (gzip, SPA-Fallback)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# statische Prototyp-Seite (eine self-contained index.html mit eingebetteten Fotos/Fonts)
COPY public/ /usr/share/nginx/html/
