#!/usr/bin/env python3
"""Build the images of the README from sample.tex.

Every figure is a grid: one row per set of options, one column per frame.
Requires lualatex, pdftoppm (poppler) and Pillow. Run from any directory:

    python3 doc/gallery/build.py [figure ...]
"""
import glob
import hashlib
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "doc", "img")
CACHE = os.path.join(HERE, ".build")
DPI = 96
GAP = 12

# name -> (frames, [(label, options), ...])
FIGURES = {
    "hero": ("title,content", [("", "")]),
    "styles": ("title,content,standout", [
        ("lamalunga", "style=lamalunga"),
        ("bauhaus", "style=bauhaus"),
        ("swiss", "style=swiss"),
        ("nordic", "style=nordic"),
        ("classical", "style=classical"),
        ("japandi", "style=japandi"),
    ]),
    "modes": ("title,content,standout", [
        ("mode=light", "mode=light"),
        ("mode=dark", "mode=dark"),
        ("mode=paper", "mode=paper"),
    ]),
    "harmonies": ("palette", [
        ("harmony=complementary", "harmony=complementary"),
        ("harmony=split", "harmony=split"),
        ("harmony=triadic", "harmony=triadic"),
        ("harmony=analogous", "harmony=analogous"),
        ("harmony=tetradic", "harmony=tetradic"),
        ("harmony=monochromatic", "harmony=monochromatic"),
    ]),
    "primaries": ("content", [
        ("primary=C0392B", "primary=C0392B"),
        ("primary=1F7A7A", "primary=1F7A7A"),
        ("primary=D4A017", "primary=D4A017"),
        ("primary=2E5EAA", "primary=2E5EAA"),
    ]),
    "wheels": ("palette", [
        ("wheel=artist", "wheel=artist"),
        ("wheel=rgb", "wheel=rgb"),
    ]),
    "contrast": ("content", [
        ("contrast=AA", "contrast=AA,primary=9B7FD4"),
        ("contrast=AAA", "contrast=AAA,primary=9B7FD4"),
    ]),
    "titles": ("title,content", [
        ("titles=plain", "titles=plain"),
        ("titles=boxed, alerts=boxed", "titles=boxed,alerts=boxed"),
    ]),
    "blocks": ("blocks", [
        ("blocks=tinted", "blocks=tinted"),
        ("blocks=tinted, corners=rounded", "blocks=tinted,corners=rounded"),
        ("blocks=rule", "blocks=rule"),
    ]),
    "bullets": ("content", [
        ("bullets=golden", "bullets=golden"),
        ("bullets=bauhaus", "bullets=bauhaus"),
    ]),
    "chrome": ("content", [
        ("footline=minimal, progressbar=frametitle",
         "footline=minimal,progressbar=frametitle"),
        ("footline=infolines, progressbar=foot",
         "footline=infolines,progressbar=foot"),
        ("headline=miniframes, footline=none",
         "headline=miniframes,footline=none,progressbar=head"),
    ]),
    "aspect": ("title", [
        ("aspect=golden", "aspect=golden"),
        ("aspect=sqrt2", "aspect=sqrt2"),
        ("aspect=beamer (16:9)", "aspect=beamer"),
    ]),
    "spiral": ("title", [
        ("spiral=true", "spiral=true"),
        ("spiral=false", "spiral=false"),
    ]),
    "guides": ("plain", [
        ("guides=both", "guides=both"),
    ]),
    "image": ("image", [("", "")]),
    "fonts": ("title", [
        ("font=plex", "font=plex"),
        ("font=source", "font=source"),
        ("font=heros", "font=heros"),
        ("font=adventor", "font=adventor"),
        ("font=garamond", "font=garamond"),
        ("font=libertinus", "font=libertinus"),
    ]),
    "margins": ("content", [
        ("margins=narrow", "margins=narrow"),
        ("margins=normal", "margins=normal"),
        ("margins=wide", "margins=wide"),
    ]),
}


def sources_digest():
    digest = hashlib.sha1()
    for path in sorted(glob.glob(os.path.join(ROOT, "*.sty"))) + [
            os.path.join(HERE, "sample.tex")]:
        with open(path, "rb") as f:
            digest.update(f.read())
    return digest.hexdigest()[:12]


def compile_row(work, name, frames, options):
    """Compile the sample with the given options, return the page images;
    a row whose sources and options did not change is not compiled again."""
    key = hashlib.sha1((SOURCES + frames + options).encode()).hexdigest()[:12]
    name = name + "-" + key
    cached = sorted(glob.glob(os.path.join(work, name + "-*.png")))
    if cached:
        return [Image.open(p).convert("RGB") for p in cached]
    cls = "[11pt,aspectratio=169]" if "aspect=beamer" in options else "[11pt]"
    source = os.path.join(work, "sample.tex")
    with open(os.path.join(HERE, "sample.tex")) as f:
        text = f.read().replace("\\documentclass[11pt]{beamer}",
                                "\\documentclass" + cls + "{beamer}")
    with open(source, "w") as f:
        f.write(text)
    env = dict(os.environ, TEXINPUTS=ROOT + "//:")
    command = ("\\def\\galleryoptions{%s}\\def\\galleryframes{%s}"
               "\\input{sample}" % (options, frames))
    for _ in range(3):
        run = subprocess.run(
            ["lualatex", "-interaction=nonstopmode", "-halt-on-error",
             "-jobname=" + name, command],
            cwd=work, env=env, capture_output=True, text=True)
        if run.returncode != 0:
            sys.exit("%s: lualatex failed\n%s" % (name, run.stdout[-2000:]))
    subprocess.run(["pdftoppm", "-r", str(DPI), "-png", name + ".pdf", name],
                   cwd=work, check=True)
    for junk in glob.glob(os.path.join(work, name + ".*")):
        os.remove(junk)
    pages = sorted(glob.glob(os.path.join(work, name + "-*.png")))
    return [Image.open(p).convert("RGB") for p in pages]


def label_font():
    for path in ("IBMPlexMono-Regular.otf", "FiraMono-Regular.otf"):
        found = subprocess.run(["kpsewhich", path], capture_output=True,
                               text=True).stdout.strip()
        if found:
            return ImageFont.truetype(found, 15)
    return ImageFont.load_default()


def build(figure):
    frames, rows = FIGURES[figure]
    os.makedirs(CACHE, exist_ok=True)
    pages = [compile_row(CACHE, "%s%d" % (figure, i), frames, options)
             for i, (_, options) in enumerate(rows)]
    # a figure of one frame per set of options is laid out as a grid of
    # cells, each with its label; otherwise one labelled row per set
    if len(frames.split(",")) == 1:
        cols = len(rows) if len(rows) <= 3 else (2 if len(rows) == 4 else 3)
        cells = [(label, row) for (label, _), row in zip(rows, pages)]
        grid = [cells[i:i + cols] for i in range(0, len(cells), cols)]
    else:
        grid = [[(label, row)] for (label, _), row in zip(rows, pages)]
    font = label_font()
    labelled = any(label for label, _ in rows)
    label_h = 26 if labelled else 0

    def cell_size(images):
        return (sum(im.width for im in images) + GAP * (len(images) - 1),
                max(im.height for im in images))

    widths = [sum(cell_size(c[1])[0] for c in line) + GAP * (len(line) - 1)
              for line in grid]
    heights = [max(cell_size(c[1])[1] for c in line) + label_h for line in grid]
    sheet = Image.new("RGBA", (max(widths), sum(heights) + GAP * (len(grid) - 1)),
                      (255, 255, 255, 0))
    draw = ImageDraw.Draw(sheet)
    y = 0
    for line, line_h in zip(grid, heights):
        x = 0
        for label, images in line:
            if labelled:
                draw.text((x, y + 3), label, font=font, fill=(120, 120, 130, 255))
            cx = x
            for im in images:
                sheet.paste(im, (cx, y + label_h))
                draw.rectangle([cx, y + label_h, cx + im.width - 1,
                                y + label_h + im.height - 1],
                               outline=(200, 200, 205, 255))
                cx += im.width + GAP
            x += cell_size(images)[0] + GAP
        y += line_h + GAP
    os.makedirs(OUT, exist_ok=True)
    sheet.save(os.path.join(OUT, figure + ".png"), optimize=True)
    print(figure, sheet.size)


SOURCES = sources_digest()

if __name__ == "__main__":
    for figure in sys.argv[1:] or FIGURES:
        build(figure)
