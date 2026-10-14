# FourenStudio

The FourenStudio website: free audio plugins by fouren.

## How it works

Each plugin is a folder in `products/` with a `product.json` describing its page, plus its images,
audio previews and download zips. `build.py` turns those into a static site in `public/`.
On GitHub, every push rebuilds and publishes the site automatically (`.github/workflows/pages.yml`).

## Add a new plugin

1. Copy `products/_template` to `products/<plugin-name>` (lower case, no spaces, e.g. `products/bloomer`).
2. Put screenshots in `images/`, audio previews (`.m4a` or `.mp3`) in `audio/`, and the zips in `downloads/`.
3. Edit `product.json`: name, text, file names, release date. The newest release date is featured on the home page.
4. Check it locally:

   ```bash
   python3 build.py
   python3 -m http.server 8765 --directory public
   ```

   then open http://localhost:8765.
5. Commit and push. The site updates on its own within a minute or two.

The build stops and lists any file a page refers to that doesn't exist, so a typo can't publish a broken link.

## Section types for product pages

| `type` | Shows |
|---|---|
| `audio` | A list of play buttons, one per preset (plus an optional dry reference) |
| `features` | A bulleted list of named features, with an optional close-up image |
| `text-image` | A close-up image followed by paragraphs |
| `gallery` | A grid of screenshots with captions |

Every section gets a heading from its `title`.

## Settings

`site.json` holds the site name, tagline, footer year, and optional contact email and social links
(empty ones are hidden).

## Credits

Fonts: Archivo Black, Barlow Condensed, IBM Plex Mono (SIL Open Font License, `assets/fonts/licenses/`).
