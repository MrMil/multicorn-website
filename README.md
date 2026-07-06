# Multicorn — מולטיקורן

The business website of **Ofer Mustigman (עפר מוסטיגמן)** — programming, 3D printing,
and custom electronics manufacturing.

- Live at: [multicorn.co.il](https://multicorn.co.il) and [mustigman.com](https://mustigman.com)
- Contact: contact@multicorn.co.il

A single static Hebrew (RTL) page, black background with magenta and purple branding.
No build step, no framework — just `index.html`, `accessibility.html`, and the assets.

## Local development

Requires Docker. From the repo root:

```sh
docker compose up
```

Then open <http://localhost:8080>. The repo folder is mounted read-only into an
`nginx:alpine` container, so any file edit is visible on browser refresh — no rebuild
needed. Stop with `docker compose down` (or Ctrl+C).

## Logo

The source artwork is `Multicorn Logo.png` — black line art of a five-horned unicorn
on a white background. The website versions (`assets/logo.png`, `assets/favicon.png`)
are generated from it by [`tools/recolor_logo.py`](tools/recolor_logo.py), which:

1. **Converts darkness to alpha** — the black artwork becomes opaque, the white
   background becomes transparent, and anti-aliased edges are preserved.
2. **Splits the artwork into connected components** (`scipy.ndimage.label`).
   The horn spirals are drawn as many small separate segments, while the head and
   mane are two large blobs — so the split is almost free.
3. **Classifies each component**: the two large blobs (head, mane) and three small
   facial details (inner ear, eye, nostril — identified by component id) are colored
   **purple** `#A06BFF`; every other component is a horn segment and is colored
   **magenta** `#FF2EB9`.
4. **Colors the semi-transparent edge pixels** by nearest component, using a
   distance transform.
5. **Crops** to the artwork with 30px padding, and also emits a 256×256 favicon.

To regenerate the assets:

```sh
python3 -m venv venv
venv/bin/pip install -r tools/requirements.txt
venv/bin/python3 tools/recolor_logo.py
```

Run with `--debug` to print every component (id, size, centroid, assigned color) and
write `debug_components.png` visualizing the classification. If the source image ever
changes, the hardcoded component ids in `PURPLE_LABELS` must be re-checked this way.

## Colors

| Role | Color |
|---|---|
| Background | `#000000` |
| Magenta (horns, headings, accents) | `#FF2EB9` |
| Purple (unicorn body, text) | `#A06BFF` |

Both text colors exceed a 6:1 contrast ratio on the black background (WCAG AA
requires 4.5:1 for normal text).

## Accessibility (נגישות)

The site follows Israeli Standard **IS 5568** (based on WCAG 2.0 level AA):

- Semantic HTML with correct `lang="he"` / `dir="rtl"`, headings, and landmarks
- Full keyboard navigation with a visible `:focus-visible` indicator
- Text contrast above the AA threshold (≥ 6:1 on black)
- `alt` text on all images
- Text scales with browser zoom (relative units, no `user-scalable` restrictions)
- Animations are disabled under `prefers-reduced-motion`
- Responsive layout for mobile and desktop

A Hebrew accessibility statement page (הצהרת נגישות, `accessibility.html`) existed
but was removed: the business currently falls under the small-business exemption in
the Equal Rights for Persons with Disabilities (Service Accessibility Adjustments)
Regulations, 5773-2013. If the business grows past the exemption threshold, restore
it from git history (`git log --all --oneline -- accessibility.html`) and re-add the
footer link in `index.html`.

## Deployment

Hosted for free on **GitHub Pages**, serving this repo's root from the `main` branch.

- `multicorn.co.il` is the primary custom domain (set in the repo's Pages settings).
- GitHub Pages allows one custom domain per repo, so `mustigman.com` is served by a
  tiny second repo whose only job is to redirect to multicorn.co.il.
- DNS for both domains is managed on DigitalOcean: four `A` records on `@` pointing
  to GitHub Pages' IPs (`185.199.108.153`, `185.199.109.153`, `185.199.110.153`,
  `185.199.111.153`) and a `www` `CNAME` to `<username>.github.io`. HTTPS
  certificates are provisioned automatically by GitHub.
