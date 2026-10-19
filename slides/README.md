# Slide deck

The talk source uses [Marp](https://marp.app/) Markdown. The content is readable without a renderer and includes speaker notes as HTML comments.

Render locally with a temporary `npx` invocation:

```sh
npx @marp-team/marp-cli@4.1.2 slides/deck.md --html --allow-local-files --output slides/deck.html
npx @marp-team/marp-cli@4.1.2 slides/deck.md --pdf --allow-local-files --output slides/root-cause-analytics-engine.pdf
```

Open `slides/deck.html` in a browser for rehearsal. Mermaid source lives in `slides/assets/*.mmd`; the matching SVG assets are embedded by the deck. Regenerate those assets before rendering if a diagram changes:

```sh
PUPPETEER_EXECUTABLE_PATH=/usr/bin/google-chrome \
  npx @mermaid-js/mermaid-cli@11.12.0 \
  -i slides/assets/evidence-plane.mmd \
  -o slides/assets/evidence-plane.svg -b transparent
```

Repeat the command for each changed `.mmd` file. For the live demo, run the terminal commands from the root `README.md` and keep Grafana and Prometheus port forwards in separate terminals.
