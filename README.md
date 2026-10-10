# Can Visual Generation Expand What Unified Multimodal Models Know?

Project page for **Knowledge Transfer Probing (KTP)**.

Wenkai Li\*, Wenyi Hong\*, Zhuoyi Yang\*, Jie Tang† — Tsinghua University · Z.AI
(\* equal contribution, † corresponding author)

Live page: https://kevinlunatic.github.io/Knowledge-Transfer-Probing/

## Structure

- `index.html` — the single-page site (header, teaser, abstract, contributions, method, experiments, conclusion, BibTeX)
- `static/images/` — figures rendered from the paper's PDF sources plus `social_preview.png` (1200×630) for link previews
- `static/pdfs/paper.pdf` — compiled paper
- `static/css/index.css` — template styles plus project-specific additions (figures, tables, contribution cards)
- `static/js/index.js` — template scripts (BibTeX copy, scroll-to-top)

## Updating

- Links to arXiv, code, and dataset are marked with `TODO` comments in `index.html`.
- To regenerate a figure from the LaTeX sources:

  ```bash
  gs -q -dNOPAUSE -dBATCH -dSAFER -sDEVICE=png16m -r220 -dUseCropBox \
     -dTextAlphaBits=4 -dGraphicsAlphaBits=4 \
     -sOutputFile=static/images/<name>.png <path-to-figures>/<name>.pdf
  ```

## Acknowledgments

Built with the [Academic Project Page Template](https://github.com/eliahuhorwitz/Academic-project-page-template), adopted from the [Nerfies](https://nerfies.github.io/) project page.

## Website License

<a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by-sa/4.0/88x31.png" /></a><br />This work is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/">Creative Commons Attribution-ShareAlike 4.0 International License</a>.
