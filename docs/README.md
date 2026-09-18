# Documentation

This directory contains the project documentation and the compiled conference
poster.

## Pages

The documentation is a small static site. Open [`pages/index.html`](pages/index.html)
to start at the overview.

The pages follow the method from motivation to application:

- `introduction.html` — why network distance matters;
- `theory.html` — directed graphs, distance matrices and the triangle-inequality screen;
- `solution.html` — the four algorithmic steps;
- `implementation.html` — Python orchestration and OSRM routing;
- `applications.html` — site, address, store and lead classification;
- `poster.html` — the concise conference-poster version.

## Assets

`pages/assets/` contains the images, Folium map and PDF used by the pages. The
poster page embeds `pages/assets/conference_poster.pdf`, which is compiled from
[`poster/conference_poster_6.tex`](poster/conference_poster_6.tex).

The pages are static and can be opened directly in a browser. A local static
server can also be used when browser security restrictions affect embedded
assets.
