# -*- coding: utf-8 -*-
"""Invert the evidence/application pairs: instruction first, citation collapsed."""
import io, os, re

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "protocol.html")
s = io.open(SRC, encoding="utf-8").read()

PAIR = re.compile(
    r'<div class="pair">\s*'
    r'<p><span class="lab">Literature insight</span>(?P<lit>.*?)</p>\s*'
    r'<p class="app"><span class="lab">Practical application</span>(?P<app>.*?)</p>\s*'
    r'</div>', re.S)

def flip(m):
    return (u'<div class="pair">\n'
            u'      <p class="app">%s</p>\n'
            u'      <details class="evidence">'
            u'<summary>The evidence behind this</summary>\n'
            u'        <p>%s</p>\n'
            u'      </details>\n'
            u'    </div>' % (m.group('app').strip(), m.group('lit').strip()))

s, n = PAIR.subn(flip, s)

OLD_CSS = u"""  .pair { display:flex; flex-direction:column; gap:.5rem; max-width:var(--measure); border-left:2px solid var(--rule-strong); padding-left:1.1rem; }
  .pair p { margin:0; font-size:.96rem; line-height:1.55; color:var(--ink-2); }
  .pair .lab { font-family:var(--f-mono); font-size:.62rem; font-weight:600; letter-spacing:.12em; text-transform:uppercase; color:var(--ink-3); display:block; margin-bottom:.15rem; }
  .pair .app { color:var(--ink); }
  .pair .app .lab { color:var(--accent); }"""

NEW_CSS = u"""  .pair { display:flex; flex-direction:column; gap:.75rem; max-width:var(--measure); border-left:3px solid var(--accent); padding-left:1.15rem; }
  .pair .app { margin:0; font-size:1.02rem; line-height:1.58; color:var(--ink); }
  .evidence { border-top:1px solid var(--rule); padding-top:.6rem; }
  .evidence summary { font-family:var(--f-mono); font-size:.62rem; font-weight:600; letter-spacing:.12em; text-transform:uppercase; color:var(--ink-3); cursor:pointer; list-style:none; display:flex; align-items:center; gap:.45rem; }
  .evidence summary::-webkit-details-marker { display:none; }
  .evidence summary::before { content:"+"; font-family:var(--f-mono); font-size:.9rem; line-height:1; width:.7em; }
  .evidence[open] summary::before { content:"\\2013"; }
  .evidence summary:hover { color:var(--accent); }
  .evidence summary:focus-visible { outline:2px solid var(--accent); outline-offset:3px; }
  .evidence p { margin:.65rem 0 0; font-size:.92rem; line-height:1.55; color:var(--ink-2); }"""

if OLD_CSS not in s:
    raise SystemExit("reorder: pair CSS block not found — nothing changed")
s = s.replace(OLD_CSS, NEW_CSS)

io.open(SRC, "w", encoding="utf-8").write(s)
print("pairs inverted: %d" % n)
print("remaining 'Literature insight' labels: %d"
      % s.count(u'Literature insight'))
