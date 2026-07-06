# -*- coding: utf-8 -*-
import re, os, io, base64, urllib.request, sys
from collections import defaultdict
from PIL import Image

SP = r"C:\Users\MATTHI~1\AppData\Local\Temp\claude\C--Projects-TeraWare-TMV\1cf0e42a-eb99-4403-be16-648dd2a65a49\scratchpad"
OUTDIR = r"C:\Projects\TeraWare\TMV\prototype"
HTML = os.path.join(SP, "all_models.html")
OUT = os.path.join(OUTDIR, "assets.js")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"}

CACHE = os.path.join(SP, "src_cache")
os.makedirs(CACHE, exist_ok=True)
def fetch(url):
    key = re.sub(r'[^A-Za-z0-9._-]', '_', url)[-140:]
    p = os.path.join(CACHE, key)
    if os.path.exists(p) and os.path.getsize(p) > 0:
        return open(p, "rb").read()
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as r:
        data = r.read()
    open(p, "wb").write(data)
    return data

def enc(data, target_w, quality, fmt="JPEG"):
    im = Image.open(io.BytesIO(data))
    if fmt == "JPEG":
        im = im.convert("RGB")
    w, h = im.size
    if w > target_w:
        im = im.resize((target_w, round(h * target_w / w)), Image.LANCZOS)
    buf = io.BytesIO()
    if fmt == "JPEG":
        im.save(buf, format="JPEG", quality=quality, optimize=True, progressive=True)
        mime = "image/jpeg"
    else:
        im.save(buf, format="PNG", optimize=True)
        mime = "image/png"
    return "data:%s;base64,%s" % (mime, base64.b64encode(buf.getvalue()).decode())

def deuml(s):
    for a, b in (("ue","ü"),("oe","ö"),("ae","ä"),("Ue","Ü"),("Oe","Ö"),("Ae","Ä")):
        s = s.replace(a, b)
    return s

# ---- parse model image variants from HTML ----
html = open(HTML, encoding="utf-8", errors="ignore").read()
urls = set(re.findall(r'https://truckmodell\.at/wp-content/uploads/2024/04/[A-Za-z0-9._-]+\.jpg', html))
groups = defaultdict(list)
for u in urls:
    fn = u.rsplit("/", 1)[1][:-4]
    m = re.search(r'-(\d+)x(\d+)$', fn)
    if m:
        base, w = fn[:m.start()], int(m.group(1))
    else:
        base, w = fn, 99999
    groups[base].append((w, u))

def pick(cands):
    cands = sorted(cands)
    for w, u in cands:
        if w >= 640:
            return u
    return cands[-1][1]

def owner_model(base):
    p = base.split("-")
    owner = (deuml(p[1]) + " " + deuml(p[0])) if len(p) >= 2 else base
    mp = p[2:]
    if mp and re.fullmatch(r'\d', mp[-1]):
        mp = mp[:-1]
    model = deuml(" ".join(mp)).replace(" .", ".").strip()
    return owner, model

models = []
bases = sorted(b for b in groups if not b.startswith("TMV-"))
print("Modelle:", len(bases), flush=True)
for i, base in enumerate(bases):
    try:
        data = fetch(pick(groups[base]))
        img = enc(data, 500, 66)
        owner, model = owner_model(base)
        if not model:
            model = base
        models.append((model, owner, img))
    except Exception as e:
        print("  skip", base, e, flush=True)
    if (i + 1) % 20 == 0:
        print("  ...", i + 1, flush=True)

# ---- hero / parcours / props / logo (explicit) ----
B = "https://truckmodell.at/wp-content/uploads/"
def try_enc(url, w, q, fmt="JPEG"):
    try:
        return enc(fetch(url), w, q, fmt)
    except Exception as e:
        print("  asset fail", url, e, flush=True)
        return ""

hero = try_enc(B + "2023/07/Bild-Startseite-min-1536x1024.jpg", 1600, 82)
parcours = []
for n in range(1, 6):
    d = try_enc(B + "2023/07/Parcours%d-1536x1024.jpg" % n, 1000, 74)
    if not d:
        d = try_enc(B + "2023/07/Parcours%d-1024x683.jpg" % n, 1000, 76)
    if d:
        parcours.append(d)
lager = try_enc(B + "2024/04/TMV-Lagerhalle-1024x768.jpg", 900, 74)
sieb = try_enc(B + "2024/04/TMV-Siebanlage-1-1024x683.jpg", 900, 74)
logo = try_enc(B + "2023/07/Logo_klein.png", 200, 0, "PNG")

def js(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'

with open(OUT, "w", encoding="utf-8") as f:
    f.write("window.TMV_ASSETS={\n")
    f.write("logo:" + js(logo) + ",\n")
    f.write("hero:" + js(hero) + ",\n")
    f.write("parcours:[" + ",".join(js(p) for p in parcours) + "],\n")
    f.write("props:{lagerhalle:" + js(lager) + ",siebanlage:" + js(sieb) + "},\n")
    f.write("models:[\n")
    for (n, o, img) in models:
        f.write("{n:" + js(n) + ",o:" + js(o) + ",img:" + js(img) + "},\n")
    f.write("]};\n")

sz = os.path.getsize(OUT)
print("OK models embedded:", len(models))
print("parcours:", len(parcours), "hero:", bool(hero), "logo:", bool(logo))
print("assets.js size: %.2f MB" % (sz / 1048576))
