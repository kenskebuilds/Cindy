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

# Force light theme: the artifact stays theme-aware, the static page does not.
# Strip the prefers-color-scheme dark block and the [data-theme="dark"] override.
head_bits = re.sub(
    r'\n  @media \(prefers-color-scheme: dark\) \{.*?\n  \}\n', u'\n',
    head_bits, flags=re.S)
head_bits = re.sub(
    r'\n  :root\[data-theme="dark"\] \{.*?\n  \}\n', u'\n',
    head_bits, flags=re.S)

# Calmer light palette for the standalone page: a real grey ground so the
# off-white cards read as surfaces, and stronger rules for separation.
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
    (u'plan',      u'The Plan',   u'Warm-up, the seven days, weekly volume',
     [u'rule', u'warmup', u'routine', u'weekly']),
    (u'reasoning', u'Reasoning',  u'Why each exercise is in, and what turned out not to matter',
     [u'selection', u'axial', u'settled']),
    (u'fuel',      u'Fuel',       u'Calories, protein, cardio for fat loss',
     [u'fatloss', u'nutrition']),
    (u'record',    u'Record',     u'How to know it worked, and what changed',
     [u'verify', u'corrections', u'ledger']),
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
<meta name="description" content="Evidence-graded 5-day training split for a fat-loss phase, with a rationale for every exercise.">
<meta name="theme-color" content="#F5F7F9">
<meta name="color-scheme" content="light">
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
io.open(os.path.join(OUT, "robots.txt"), "w", encoding="utf-8").write(
    u"User-agent: *\nDisallow: /\n")
io.open(os.path.join(OUT, ".nojekyll"), "w", encoding="utf-8").write(u"")
io.open(os.path.join(OUT, "README.md"), "w", encoding="utf-8").write(
    u"# The Zero-Waste Protocol\n\n"
    u"A 5-day training split built for a fat-loss phase, with every recommendation traced to "
    u"peer-reviewed literature and the weak spots marked rather than smoothed over.\n\n"
    u"Open `index.html`, or serve via GitHub Pages.\n\n"
    u"## Notes\n\n"
    u"- `robots.txt` and a `noindex` meta tag are included to discourage search indexing. "
    u"They are not access control \u2014 anything on a public GitHub Pages site is publicly readable.\n"
    u"- Single self-contained file. The only external request is Google Fonts.\n"
    u"- General training and nutrition analysis, not medical advice.\n")

print("built ->", OUT)
print("index.html bytes:", os.path.getsize(os.path.join(OUT, "index.html")))
