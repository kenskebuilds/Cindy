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
<style>%s</style>
%s
</head>
<body>
%s
<p style="max-width:62rem;margin:0 auto;padding:0 clamp(1.1rem,4vw,2.75rem) 3rem;font-family:'IBM Plex Mono',ui-monospace,monospace;font-size:.7rem;color:var(--ink-3)">Last built %s</p>
</body>
</html>
""" % (FAVICON, FAVICON, title, RESET, head_bits.strip(), body.rstrip(), stamp)

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
