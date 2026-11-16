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
# Group the sections into tabs. Weekly volume lands first (how the exercises
# add up per muscle), then the plan; everything that explains or audits it
# sits behind the nav.
TABS = [
    (u'volume',      u'Weekly Volume', u'Weekly sets per muscle, and the exercises that add up to them',
     [u'weekly']),
    (u'plan',        u'The Plan',    u'Warm-up and the five lifting days',
     [u'warmup', u'routine']),
    (u'fourday',     u'4-Day Variant', u'98 sets in four sessions, against the five-day’s 99 — a near volume-matched trial plan that co-exists with the five-day',
     [u'fourday']),
    (u'progression', u'Progression', u'Loading tiers, the four-week block, when to change what',
     [u'loading', u'block', u'progress']),
    (u'fuel',        u'Cardio &amp; support', u'Cardio placement, nutrition pointer, supplements, adherence',
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

# ------------------------------------------------------- drift check ----
# The Weekly Volume tiles are hand-maintained markup, so check them before
# anything is written. Three sources must agree, or the build stops:
#   1. the five-day Weekly totals table (direct and effective per muscle),
#   2. the tiles in each muscle row (solid = 1 per set, dashed = 1/2 per set)
#      and the "direct + indirect = total" figures printed beside them, plus the
#      frequency (days with direct tiles), the D1-D5 strip and the bar beside them,
#   3. the routine tables (each tile's day, exercise and set count).
# Tiles use a few shortened exercise names; map them back to the routine's.
TILE_NAMES = {
    u'Smith Lunge': u'Smith Machine Lunge',
    u'Overhead Cable Extension': u'Seated Overhead Cable Extension',
    u'Cable Hammer Curl': u'Hammer Curl (Cable)',
    u'Flat DB Bench Press': u'Flat Dumbbell Bench Press',
}

def _num(text):
    """'13' -> 13.0, '6½' -> 6.5, '13.5' -> 13.5; None if it is not a number."""
    t = text.strip()
    half = t.endswith(u'½')
    if half:
        t = t[:-1] or u'0'
    try:
        return float(t) + (0.5 if half else 0.0)
    except ValueError:
        return None

def _fmt(n):
    return (u'%g' % n)

def check_volume_drift():
    errors = []
    weekly, routine = sections[u'weekly'], sections[u'routine']

    table = {}
    table_freq = {}
    for m in re.finditer(r'<tr><td class="c-move">([^<]*)</td><td class="c-load">([^<]*)</td>'
                         r'<td class="c-load">([^<]*)</td><td class="c-rir">(\d)×</td>', weekly):
        table[m.group(1)] = (_num(m.group(2)), _num(m.group(3)))
        table_freq[m.group(1)] = int(m.group(4))
    if not table:
        return [u'could not find the Weekly totals table in section "weekly"']

    sessions = {}
    day = None
    for m in re.finditer(r'session-day">Day (\d)<|<td class="c-move">(.*?)<small>.*?</small></td>'
                         r'\s*<td class="c-target">.*?</td>\s*<td class="c-load">(\d+) ×', routine):
        if m.group(1):
            day = int(m.group(1))
            continue
        key = (day, m.group(2).strip())
        if key in sessions:
            errors.append(u'routine: Day %d lists "%s" twice; the tile check cannot tell them apart'
                          % key)
        sessions[key] = int(m.group(3))
    if not sessions:
        errors.append(u'could not read any exercises from the routine tables')
    used = set()

    rows = list(re.finditer(r'<div class="vm-row" data-muscle="([^"]*)">(.*?)</ul>', weekly, re.S))
    if len(rows) != weekly.count(u'<div class="vm-row"'):
        errors.append(u'a Weekly Volume row is missing its data-muscle attribute or its tile list')
    seen = set()
    for row in rows:
        muscle, html = row.group(1), row.group(2)
        seen.add(muscle)
        direct = indirect = 0.0
        tiles = list(re.finditer(
            r'<li class="vm-x( is-half)?"><b class="vm-day">D(\d)</b><span class="vm-ex">([^<]*)</span>'
            r'<span class="vm-sets">([^<]*)</span></li>', html))
        if len(tiles) != html.count(u'<li'):
            errors.append(u'%s: a tile is malformed (expected <li class="vm-x"> with day, name and sets)'
                          % muscle)
        for t in tiles:
            half, tday, name, sets_txt = bool(t.group(1)), int(t.group(2)), t.group(3), t.group(4)
            sm = re.match(u'^(\\d+)( × ½)?$', sets_txt.strip())
            if not sm or bool(sm.group(2)) != half:
                errors.append(u'%s: tile "D%d %s" has set count "%s"; expected a whole number%s'
                              % (muscle, tday, name, sets_txt, u' followed by " × ½" (dashed tile)'
                                 if half else u' (solid tile)'))
                continue
            sets = int(sm.group(1))
            if half:
                indirect += sets / 2.0
            else:
                direct += sets
            full = TILE_NAMES.get(name, name)
            if (tday, full) not in sessions:
                errors.append(u'%s: tile "D%d %s" has no matching exercise on Day %d of the routine'
                              % (muscle, tday, name, tday))
            elif sessions[(tday, full)] != sets:
                errors.append(u'%s: tile "D%d %s" shows %d sets; the routine has %d'
                              % (muscle, tday, name, sets, sessions[(tday, full)]))
            used.add((tday, full))

        if muscle not in table:
            errors.append(u'%s: has a Weekly Volume row but no line in the Weekly totals table' % muscle)
            continue
        t_direct, t_eff = table[muscle]
        if direct != t_direct:
            errors.append(u'%s: solid tiles add up to %s direct sets; the table says %s'
                          % (muscle, _fmt(direct), _fmt(t_direct)))
        if direct + indirect != t_eff:
            errors.append(u'%s: tiles add up to %s total (%s direct + %s indirect); the table\'s effective is %s'
                          % (muscle, _fmt(direct + indirect), _fmt(direct), _fmt(indirect), _fmt(t_eff)))
        # Frequency rule: "x a week" = number of days with DIRECT (solid) tiles. Days with only
        # dashed tiles are half credit and do not count. The day strip must show the same days.
        solid_days = sorted({int(t.group(2)) for t in tiles if not t.group(1)})
        half_days = sorted({int(t.group(2)) for t in tiles if t.group(1)} - set(solid_days))
        fm = re.search(u'vm-freq">(\\d)× a week', html)
        if not fm or int(fm.group(1)) != len(solid_days):
            errors.append(u'%s: the row says %s× a week; direct sets fall on %d day(s) (%s)'
                          % (muscle, fm.group(1) if fm else u'(missing)', len(solid_days),
                             u', '.join(u'D%d' % d for d in solid_days)))
        if table_freq.get(muscle) != len(solid_days):
            errors.append(u'%s: the Weekly totals table says %s×; direct sets fall on %d day(s)'
                          % (muscle, table_freq.get(muscle), len(solid_days)))
        strip = re.findall(u'<i class="vm-d( is-full| is-half)?">(\\d)</i>', html)
        strip_full = sorted(int(n) for c, n in strip if c == u' is-full')
        strip_half = sorted(int(n) for c, n in strip if c == u' is-half')
        if strip_full != solid_days or strip_half != half_days:
            errors.append(u'%s: the D1-D5 strip shows direct on %s and indirect-only on %s; the tiles say %s and %s'
                          % (muscle, strip_full, strip_half, solid_days, half_days))
        bar = re.search(u'vm-bar" role="img" aria-label="([^"]*?) total sets', html)
        fills = re.findall(u'vm-fill( is-half)?" style="([^"]*)"', html)
        want_fills = [(u'', u'width:%g%%' % (direct * 5))]
        if indirect:
            want_fills.append((u' is-half', u'left:%g%%;width:%g%%' % (direct * 5, indirect * 5)))
        if not bar or _num(bar.group(1)) != direct + indirect or fills != want_fills:
            errors.append(u'%s: the bar (label "%s", fills %s) does not match %s total on the 0-20 scale'
                          % (muscle, bar.group(1) if bar else u'(missing)', fills, _fmt(direct + indirect)))
        for cls, want in ((u'is-direct', direct), (u'is-indirect', indirect), (u'is-total', direct + indirect)):
            fm = re.search(u'vm-term %s[^"]*"><b>([^<]*)</b>' % cls, html)
            shown = _num(fm.group(1)) if fm else None
            if shown != want:
                errors.append(u'%s: the printed %s figure is "%s" but the tiles add up to %s'
                              % (muscle, cls[3:], fm.group(1) if fm else u'(missing)', _fmt(want)))

    for muscle in table:
        if muscle not in seen:
            errors.append(u'%s: is in the Weekly totals table but has no Weekly Volume row' % muscle)
    for key in sorted(set(sessions) - used):
        errors.append(u'routine: Day %d "%s" (%d sets) is not credited to any muscle on the Weekly Volume tab'
                      % (key[0], key[1], sessions[key]))
    return errors

drift = check_volume_drift()
if drift:
    raise SystemExit(u"build: Weekly Volume tab does not match the Weekly totals table or the routine. "
                     u"Nothing was written.\n  - " + u"\n  - ".join(drift))

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
      show(t.dataset.tab, true); // switch panel only; keep scroll position
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
    u"# The Deficit Hypertrophy Protocol\n\nA 5-day training split for a 40-year-old intermediate-advanced lifter in a caloric deficit. Primary outcome is hypertrophy; fat loss is secondary and handled by the diet. Every dose is traced to a citation, every citation is graded high/medium/low, and the plan is checked against fifteen explicit constraints in a validation report rather than asserted.\n\nOpen `index.html`, or serve via GitHub Pages. `build.py` emits two files from the same source: `index.html` for GitHub Pages and `artifact.html` (a head/body-less fragment) for claude.ai.\n\n## Build\n\n    python build.py\n\nSource of truth is `src/protocol.html`. `build.py` wraps it into the standalone page and groups the sections into tabs. Both outputs follow the viewer's system theme; the standalone page additionally swaps in a slightly deeper *light* palette so the off-white cards read as surfaces against a grey ground. Every section must be assigned to a tab in `TABS` or the build aborts.\n\n## Notes\n\n- `robots.txt` and a `noindex` meta tag are included to discourage search indexing. They are not access control - anything on a public GitHub Pages site is publicly readable.\n- Single self-contained file. The only external request is Google Fonts.\n- General training and nutrition analysis, not medical advice.\n")
