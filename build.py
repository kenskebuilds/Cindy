# -*- coding: utf-8 -*-
"""Wrap the artifact fragment into a standalone static page for GitHub Pages."""
import io, os, re, datetime

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "protocol.html")
OUT = os.path.dirname(os.path.abspath(__file__))

frag = io.open(SRC, encoding="utf-8").read()

# Split head-ish bits (title/link/style) from body content (first <div class="wrap">)
i = frag.index(u'<div class="wrap">')
head_bits, body = frag[:i], frag[i:]

title = re.search(r'<title>([^<]*)</title>', head_bits).group(1)
head_bits = head_bits.replace(u'<title>%s</title>' % title, u'')

# Both builds keep the head exactly as authored, including the dark-theme blocks.
# head_themed is the artifact's copy: authored palette, untouched.
head_themed = head_bits

# The static page follows the viewer's system theme too - it is NOT forced light.
# What it does change is the *light* palette: a real grey ground so the off-white
# cards read as surfaces, and stronger rules for separation. None of these tokens
# appear inside the dark blocks, so the swap leaves dark mode untouched.
TONED = [
    (u'--ground:#F5F7F9',     u'--ground:#E7ECF1'),
    (u'--surface:#FFFFFF',    u'--surface:#F9FBFC'),
    (u'--surface-2:#EDF1F4',  u'--surface-2:#DDE4EB'),
    (u'--ink:#131A22',        u'--ink:#0F151B'),
    (u'--ink-2:#4A5563',      u'--ink-2:#3F4954'),
    (u'--ink-3:#78838F',      u'--ink-3:#69747F'),
    (u'--rule:#DCE2E8',       u'--rule:#CCD5DD'),
    (u'--rule-strong:#C3CCD5', u'--rule-strong:#AEB9C4'),
    (u'--accent-soft:#E2EDF3', u'--accent-soft:#D6E4EC'),
    (u'--cut-soft:#F7E8E8',   u'--cut-soft:#F2DCDC'),
    (u'--keep-soft:#E3EEEA',  u'--keep-soft:#D7E7E1'),
    (u'--swap-soft:#F5ECDD',  u'--swap-soft:#EFE2CE'),
]
for old, new in TONED:
    head_bits = head_bits.replace(old, new)

# ---------------------------------------------------------------- tabs ----
# Group the sections into four tabs. The plan lands first; everything that
# explains or audits it sits behind the nav.
TABS = [
    (u'plan',        u'The Plan',    u'Warm-up, the seven days, weekly volume',
     [u'warmup', u'routine', u'weekly']),
    (u'fourday',     u'4-Day Variant', u'The same 98 sets in four sessions — a volume-matched trial plan that co-exists with the five-day',
     [u'fourday']),
    (u'progression', u'Progression', u'Loading tiers, the four-week block, when to change what',
     [u'loading', u'block', u'progress']),
    (u'fuel',        u'Fuel',        u'Cardio placement, calories, protein, supplements, adherence',
     [u'cardio', u'nutrition', u'supplements', u'adherence']),
    (u'evidence',    u'Evidence',    u'The one rule, every citation graded, what the evidence overturns, and the constraints checked',
     [u'rule', u'challenge', u'appendix', u'validation', u'practical']),
]

masthead = re.search(r'  <header class="masthead">.*?\n  </header>\n', body, re.S).group(0)
footer   = re.search(r'  <footer>.*?</footer>\n', body, re.S).group(0)

sections = {}
for m in re.finditer(r'  <section id="([a-z]+)">.*?\n  </section>\n', body, re.S):
    sections[m.group(1)] = m.group(0)

missing = [i for _, _, _, ids in TABS for i in ids if i not in sections]
if missing:
    raise SystemExit("build: sections not found: %s" % missing)
orphans = [k for k in sections if k not in [i for _, _, _, ids in TABS for i in ids]]
if orphans:
    raise SystemExit("build: sections not assigned to any tab: %s" % orphans)

nav = [u'  <nav class="tabs" aria-label="Sections">']
for slug, label, blurb, _ in TABS:
    nav.append(u'    <button type="button" class="tab" data-tab="%s" '
               u'aria-selected="false" title="%s">%s</button>' % (slug, blurb, label))
nav.append(u'    <button type="button" id="ev-toggle" class="tab ev-toggle" '
           u'aria-pressed="false">Show evidence</button>')
nav.append(u'  </nav>')
nav = u'\n'.join(nav) + u'\n'

panels = []
for slug, label, blurb, ids in TABS:
    panels.append(u'  <div class="panel" id="%s" role="region" aria-label="%s">' % (slug, label))
    panels.append(u'    <p class="panel-blurb">%s</p>' % blurb)
    panels.extend(sections[i].rstrip(u'\n') for i in ids)
    panels.append(u'  </div>')
panels = u'\n'.join(panels) + u'\n'

body = u'<div class="wrap">\n' + masthead + nav + panels + footer + u'</div>\n'

TAB_CSS = u"""
  .tabs { position:sticky; top:0; z-index:20; display:flex; gap:.15rem;
    margin:0 calc(var(--pad) * -1); padding:0 var(--pad);
    background:color-mix(in srgb, var(--ground) 92%, transparent);
    backdrop-filter:saturate(1.4) blur(10px);
    border-bottom:1px solid var(--rule-strong);
    overflow-x:auto; scrollbar-width:none; }
  .tabs::-webkit-scrollbar { display:none; }
  .tab { appearance:none; background:none; border:0; border-bottom:2px solid transparent;
    font-family:var(--f-mono); font-size:.7rem; font-weight:600; letter-spacing:.11em;
    text-transform:uppercase; color:var(--ink-3); cursor:pointer;
    padding:.95rem .85rem; white-space:nowrap; transition:color .12s, border-color .12s; }
  .tab:hover { color:var(--ink-2); }
  .tab[aria-selected="true"] { color:var(--accent); border-bottom-color:var(--accent); }
  .panel-blurb { font-family:var(--f-mono); font-size:.7rem; letter-spacing:.02em;
    color:var(--ink-3); margin:0; }
  .panel { display:flex; flex-direction:column; gap:3.25rem; }
  body.js .panel[hidden] { display:none; }
  .panel > section:first-of-type .sec-head { border-top:0; padding-top:0; }
  /* Let the workout tables break out past the reading column on wide screens.
     Prose stays at a readable measure; only the tables go wide. Below ~1200px
     they fall back to scrolling inside .scroller, exactly as on mobile. */
  #routine .scroller { width:min(94vw, 1320px); margin-left:50%; transform:translateX(-50%); }
  #routine table { min-width:1120px; }
  #routine .c-why { min-width:17rem; }
  #routine .c-cue { min-width:14rem; }
  @media (max-width:64rem) { #routine .scroller { width:auto; margin-left:0; transform:none; } }
  .ev-toggle { margin-left:auto; color:var(--ink-3); border-bottom-color:transparent; }
  .ev-toggle::before { content:"+"; margin-right:.4rem; }
  .ev-toggle[aria-pressed="true"] { color:var(--accent); }
  .ev-toggle[aria-pressed="true"]::before { content:"\\2013"; }
  @media (max-width:40rem) { .tab { padding:.85rem .6rem; font-size:.65rem; }
    .ev-toggle { margin-left:.5rem; } }
"""

TAB_JS = u"""
<script>
(function () {
  var b = document.body; b.classList.add('js');
  var tabs = [].slice.call(document.querySelectorAll('.tab[data-tab]'));
  var panels = [].slice.call(document.querySelectorAll('.panel'));
  function show(slug, push) {
    if (!document.getElementById(slug)) slug = tabs[0].dataset.tab;
    panels.forEach(function (p) { p.hidden = (p.id !== slug); });
    tabs.forEach(function (t) { t.setAttribute('aria-selected', t.dataset.tab === slug); });
    if (push && location.hash.slice(1) !== slug) history.pushState(null, '', '#' + slug);
  }
  tabs.forEach(function (t) {
    t.addEventListener('click', function () {
      show(t.dataset.tab, true);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  });
  window.addEventListener('popstate', function () { show(location.hash.slice(1), false); });
  // In-page links to another tab's panel (e.g. href="#fourday") change the hash
  // without a popstate, so the panel would stay hidden. Switch tabs on hashchange too.
  window.addEventListener('hashchange', function () {
    show(location.hash.slice(1), false);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
  show(location.hash.slice(1) || tabs[0].dataset.tab, false);

  var ev = document.getElementById('ev-toggle');
  var boxes = [].slice.call(document.querySelectorAll('details.evidence'));
  ev.addEventListener('click', function (e) {
    e.preventDefault();
    var open = ev.getAttribute('aria-pressed') !== 'true';
    // Hold scroll position. Anchor to the section you are currently reading —
    // sections are stable containers, unlike anything inside a box that is
    // itself expanding.
    var blocks = [].slice.call(
      document.querySelectorAll('.panel:not([hidden]) > section > *'));
    var anchor = null, before = 0;
    blocks.forEach(function (el) {
      var top = el.getBoundingClientRect().top;
      if (top <= 120) { anchor = el; before = top; }
    });
    boxes.forEach(function (d) { d.open = open; });
    ev.setAttribute('aria-pressed', open);
    ev.textContent = open ? 'Hide evidence' : 'Show evidence';
    if (anchor) { window.scrollBy(0, anchor.getBoundingClientRect().top - before); }
  });
})();
</script>
"""

RESET = u"""
  :root{color-scheme:light dark}
  *,*::before,*::after{box-sizing:border-box}
  html{-webkit-text-size-adjust:100%}
  body{margin:0}
  img,svg,video{max-width:100%;height:auto}
  table{border-collapse:collapse}
"""

FAVICON = (u'data:image/svg+xml,'
           u'%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22%3E'
           u'%3Ctext y=%22.9em%22 font-size=%2290%22%3E%F0%9F%8F%8B%3C/text%3E%3C/svg%3E')

stamp = datetime.date.today().isoformat()

page = u"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<meta name="description" content="Citation-graded 5-day hypertrophy protocol for a lifter in a caloric deficit, built around a lumbar loading budget.">
<meta name="theme-color" content="#E7ECF1" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0F1418" media="(prefers-color-scheme: dark)">
<meta name="color-scheme" content="light dark">
<link rel="icon" href="%s">
<link rel="apple-touch-icon" href="%s">
<title>%s</title>
<style>%s%s</style>
%s
</head>
<body>
%s
<p style="max-width:62rem;margin:0 auto;padding:0 clamp(1.1rem,4vw,2.75rem) 3rem;font-family:'IBM Plex Mono',ui-monospace,monospace;font-size:.7rem;color:var(--ink-3)">Last built %s</p>
</body>
</html>
""" % (FAVICON, FAVICON, title, RESET, TAB_CSS, head_bits.strip(), body.rstrip(), stamp + TAB_JS)

if not os.path.isdir(OUT):
    os.makedirs(OUT)

io.open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(page)

# ---------------------------------------------------------- artifact ----
# Same tabs, same JS, same content - but as a fragment for claude.ai/code,
# which supplies its own <!doctype>, <head> and reset at publish time. So no
# doctype wrapper, no RESET, no light-theme forcing: the page follows the
# viewer's theme, which is why head_themed is used rather than head_bits.
# Written on every build so it can never drift from index.html.
art_head = head_themed.strip()
if not art_head.endswith(u"</style>"):
    raise SystemExit("build: expected the source head to end with </style>")
cut = art_head.rfind(u"</style>")
art_head = art_head[:cut] + TAB_CSS + art_head[cut:]

artifact = u"""<title>%s</title>
%s

%s%s
""" % (
    title, art_head, body.rstrip(), TAB_JS)

io.open(os.path.join(OUT, "artifact.html"), "w", encoding="utf-8").write(artifact)
io.open(os.path.join(OUT, "robots.txt"), "w", encoding="utf-8").write(
    u"User-agent: *\nDisallow: /\n")
io.open(os.path.join(OUT, ".nojekyll"), "w", encoding="utf-8").write(u"")
io.open(os.path.join(OUT, "README.md"), "w", encoding="utf-8").write(
    u"# The Deficit Hypertrophy Protocol\n\nA 5-day training split for a 40-year-old intermediate-advanced lifter in a caloric deficit. Primary outcome is hypertrophy; fat loss is secondary and handled by the diet. Every dose is traced to a citation, every citation is graded high/medium/low, and the plan is checked against nine explicit constraints in a validation report rather than asserted.\n\nOpen `index.html`, or serve via GitHub Pages. `build.py` emits two files from the same source: `index.html` for GitHub Pages and `artifact.html` (a head/body-less fragment) for claude.ai.\n\n## Build\n\n    python build.py\n\nSource of truth is `src/protocol.html`. `build.py` wraps it into the standalone page and groups the sections into tabs. Both outputs follow the viewer's system theme; the standalone page additionally swaps in a slightly deeper *light* palette so the off-white cards read as surfaces against a grey ground. Every section must be assigned to a tab in `TABS` or the build aborts.\n\n## Notes\n\n- `robots.txt` and a `noindex` meta tag are included to discourage search indexing. They are not access control - anything on a public GitHub Pages site is publicly readable.\n- Single self-contained file. The only external request is Google Fonts.\n- General training and nutrition analysis, not medical advice.\n")
