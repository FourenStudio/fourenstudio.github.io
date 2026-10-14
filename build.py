#!/usr/bin/env python3
"""Builds the FourenStudio website into public/.

Every folder in products/ with a product.json becomes a plugin page at /plugins/<folder>/ and a card
on the home page (newest first). Only the Python standard library is used.

    python3 build.py           # build into public/
    (the build stops with a list if any file a page links to is missing)
"""

import html
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "public"
PRODUCTS = ROOT / "products"

esc = html.escape


# ---------------------------------------------------------------------------------------------
# Content loading


def load_site():
    return json.loads((ROOT / "site.json").read_text(encoding="utf-8"))


def load_products():
    products = []
    for folder in sorted(PRODUCTS.iterdir()):
        spec = folder / "product.json"
        if folder.name.startswith("_") or not spec.exists():
            continue  # folders starting with _ (like _template) are skipped
        product = json.loads(spec.read_text(encoding="utf-8"))
        product["slug"] = folder.name
        product["dir"] = folder
        products.append(product)
    # newest first; "order" breaks ties and lets you pin a plugin
    products.sort(key=lambda p: (p.get("released", ""), -p.get("order", 0)), reverse=True)
    return products


def files_referenced(product):
    """Every file inside the product folder that its page links to."""
    refs = [product.get("hero"), product.get("card"), product.get("wordmark")]
    for section in product.get("sections", []):
        refs.append(section.get("image"))
        if section.get("reference"):
            refs.append(section["reference"]["file"])
        refs += [item.get("file") for item in section.get("items", [])]
        refs += [img["file"] for img in section.get("images", [])]
    refs += [d["file"] for d in product.get("downloads", [])]
    return [r for r in refs if r]


# ---------------------------------------------------------------------------------------------
# Small HTML pieces


def section_title(text):
    return f'<h2 class="section-title">{esc(text)}</h2>'


def wave_divider():
    return '<div class="waves" aria-hidden="true"><svg class="waves-svg" preserveAspectRatio="none"></svg></div>'


def page(site, title, description, body, depth, og_image=None):
    up = "../" * depth
    og = f'<meta property="og:image" content="{esc(og_image)}">' if og_image else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
{og}
<link rel="icon" href="{up}assets/brand/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{up}assets/style.css">
</head>
<body>
<header class="site-header">
  <a class="brand" href="{up}index.html" aria-label="{esc(site['name'])} home">
    <span class="brand-top">FOUREN</span><span class="brand-bottom">STUDIO</span>
  </a>
  <nav><a href="{up}index.html#plugins">PLUGINS</a></nav>
</header>
<main>
{body}
</main>
<footer class="site-footer">
  <span>© {esc(site['year'])}, {esc(site['name'])}</span>
  {footer_links(site)}
</footer>
<script src="{up}assets/site.js"></script>
</body>
</html>
"""


def footer_links(site):
    links = []
    if site.get("contact_email"):
        links.append(f'<a href="mailto:{esc(site["contact_email"])}">Contact</a>')
    for name, url in site.get("social", {}).items():
        if url:
            links.append(f'<a href="{esc(url)}" rel="noopener">{esc(name)}</a>')
    return "".join(links)


def product_title(product, prefix, heading="h1"):
    if product.get("wordmark"):
        return (f'<{heading} class="product-name"><img class="wordmark" src="{prefix}{esc(product["wordmark"])}" '
                f'alt="{esc(product["name"])}"></{heading}>')
    return f'<{heading} class="product-name">{esc(product["name"])}</{heading}>'


def hero(product, prefix, link_to=None):
    """Big framed screenshot, then name, price and the button (like a hardware product shot)."""
    shot = f'<img src="{prefix}{esc(product["hero"])}" alt="{esc(product["name"])} plugin interface" width="1800" height="1064">'
    if link_to:
        shot = f'<a href="{link_to}">{shot}</a>'
    button_href = link_to + "#download" if link_to else "#download"
    return f"""
<section class="hero">
  <div class="hero-frame">{shot}</div>
  <div class="hero-meta">
    <div>
      {product_title(product, prefix, "h1" if not link_to else "h2")}
      <p class="small">{esc(product["formats"])}</p>
      <p class="small">{esc(product["compatibility"])}</p>
    </div>
    <div class="hero-buy">
      <span class="price">{esc(product["price"])}</span>
      <a class="pill" href="{button_href}">DOWNLOAD</a>
    </div>
  </div>
</section>"""


# ---------------------------------------------------------------------------------------------
# Product page sections


def section_audio(s):
    rows = []
    entries = ([dict(s["reference"], note="No effect", ref=True)] if s.get("reference") else []) + s["items"]
    for item in entries:
        cls = "track ref" if item.get("ref") else "track"
        rows.append(f"""
      <li class="{cls}">
        <button class="play" aria-label="Play {esc(item['name'])}" data-src="{esc(item['file'])}"></button>
        <div class="track-text"><span class="track-name">{esc(item['name'])}</span><span class="track-note">{esc(item.get('note', ''))}</span></div>
        <div class="track-bar"><span></span></div>
      </li>""")
    return f"""
<section class="content">
  {section_title(s['title'])}
  <p class="lead">{esc(s.get('text', ''))}</p>
  <ul class="tracks">{''.join(rows)}
  </ul>
</section>"""


def section_features(s):
    items = "".join(f"<div><dt>{esc(i['name'])}</dt><dd>{esc(i['text'])}</dd></div>" for i in s["items"])
    image = f'<div class="detail"><img src="{esc(s["image"])}" alt="" loading="lazy"></div>' if s.get("image") else ""
    return f"""
<section class="content">
  {section_title(s['title'])}
  <p class="lead">{esc(s.get('text', ''))}</p>
  {image}
  <dl class="features">{items}</dl>
</section>"""


def section_text_image(s):
    paras = "".join(f"<p>{esc(t)}</p>" for t in s["text"])
    return f"""
<section class="content">
  {section_title(s['title'])}
  <div class="detail"><img src="{esc(s['image'])}" alt="" loading="lazy"></div>
  <div class="prose">{paras}</div>
</section>"""


def section_gallery(s):
    figs = "".join(f'<figure><img src="{esc(i["file"])}" alt="{esc(i.get("caption", ""))}" loading="lazy">'
                   f'<figcaption>{esc(i.get("caption", ""))}</figcaption></figure>' for i in s["images"])
    return f"""
<section class="content wide">
  {section_title(s['title'])}
  <div class="gallery">{figs}</div>
</section>"""


SECTIONS = {"audio": section_audio, "features": section_features, "text-image": section_text_image, "gallery": section_gallery}


def section_specs(product):
    cols = "".join(f'<div><h3>{esc(platform)}</h3><ul>{"".join(f"<li>{esc(x)}</li>" for x in lines)}</ul></div>'
                   for platform, lines in product.get("specs", {}).items())
    return f"""
<section class="content wide">
  <div class="card specs"><h2>SPECS</h2><div class="cols">{cols}</div></div>
</section>"""


def section_download(product):
    buttons = []
    for d in product.get("downloads", []):
        if d.get("file"):
            buttons.append(f'<a class="pill big" href="{esc(d["file"])}" download>Download for {esc(d["platform"])}'
                           f'<small>{esc(d.get("note", ""))}</small></a>')
        else:
            buttons.append(f'<span class="pill big disabled">{esc(d["platform"])}<small>{esc(d.get("note", ""))}</small></span>')

    guides = []
    for platform, steps in product.get("install", {}).items():
        lis = []
        for step in steps:
            code = ""
            if step.get("code"):
                code = (f'<div class="code"><code>{esc(step["code"])}</code>'
                        f'<button class="copy" data-copy="{esc(step["code"])}">Copy</button></div>')
            lis.append(f"<li><p>{esc(step['text'])}</p>{code}</li>")
        guides.append(f'<div class="card install"><h3>Install on {esc(platform)}</h3><ol>{"".join(lis)}</ol></div>')

    return f"""
<section class="content" id="download">
  {section_title("Download")}
  <p class="lead">Free. Version {esc(product['version'])}.</p>
  <div class="downloads">{''.join(buttons)}</div>
  <div class="installs">{''.join(guides)}</div>
</section>"""


def product_page(site, product):
    body = [hero(product, ""), wave_divider()]
    body += [f'<section class="content"><div class="prose intro">{"".join(f"<p>{esc(t)}</p>" for t in product["intro"])}</div></section>']
    for s in product.get("sections", []):
        body.append(SECTIONS[s["type"]](s))
    body.append(section_specs(product))
    body.append(section_download(product))
    return page(site, f"{product['name']} · {site['name']}", product["tagline"], "\n".join(body), 2, product["hero"])


def home_page(site, products):
    featured = products[0]
    cards = "".join(f"""
    <a class="product-card" href="plugins/{p['slug']}/index.html">
      <img src="plugins/{p['slug']}/{esc(p['card'])}" alt="" loading="lazy">
      <div class="card-meta"><span class="card-name">{esc(p['name'])}</span><span class="price">{esc(p['price'])}</span></div>
      <p class="small">{esc(p['tagline'])}</p>
    </a>""" for p in products)
    body = f"""
<section class="intro-line"><p>{esc(site['tagline'])}</p></section>
{hero(featured, f"plugins/{featured['slug']}/", link_to=f"plugins/{featured['slug']}/index.html")}
{wave_divider()}
<section class="content wide" id="plugins">
  {section_title("Plugins")}
  <div class="product-grid">{cards}
  </div>
</section>"""
    return page(site, f"{site['name']} · {site['tagline']}", site["tagline"], body, 0)


# ---------------------------------------------------------------------------------------------


def build():
    site = load_site()
    products = load_products()
    if not products:
        sys.exit("No products found in products/ (each needs a product.json).")

    missing = [f"products/{p['slug']}/{ref}" for p in products for ref in files_referenced(p) if not (p["dir"] / ref).exists()]
    if missing:
        sys.exit("Missing files:\n  " + "\n  ".join(missing))

    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "assets", OUT / "assets")

    for p in products:
        dest = OUT / "plugins" / p["slug"]
        shutil.copytree(p["dir"], dest, ignore=shutil.ignore_patterns("product.json", ".*"))
        (dest / "index.html").write_text(product_page(site, p), encoding="utf-8")

    (OUT / "index.html").write_text(home_page(site, products), encoding="utf-8")
    (OUT / ".nojekyll").write_text("")  # GitHub Pages: serve files as they are
    print(f"Built {len(products)} plugin page(s) into {OUT.relative_to(ROOT)}/")


if __name__ == "__main__":
    build()
