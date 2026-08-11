# BesoGo provenance

The files in this directory are the minimal Go-board runtime vendored from
[yewang/besogo](https://github.com/yewang/besogo) at commit
`4f03a3a04bc632c49ca9b494cbcad5c7cfb3f6b2` (version `0.0.2-alpha`).

Only the eight JavaScript sources required for parsing and displaying SGF game
trees are included, together with the flat SVG board theme. BesoGo's panels,
file tooling, and raster image assets are intentionally omitted. The vendored
`besogo.js` is a board-only downstream adaptation: its panel factory,
auto-initialization, XHR loading, wheel handler, and panel-aware resizing paths
were removed. SGF fetching, validation, and responsive sizing live in the site
wrapper. The other upstream sources are unmodified. All files remain covered
by the adjacent MIT `LICENSE`.
