# Sarasa Term — r404r custom build

> [!IMPORTANT]
> This is an **unofficial personal fork** of
> [be5invis/Sarasa-Gothic](https://github.com/be5invis/Sarasa-Gothic), used for
> font research, custom builds, and releases. For the original project and its
> complete family/region selection, please use the upstream repository.

This fork focuses on a compact terminal-font distribution with a custom-built
Iosevka Latin set and an optional, fidelity-checked Nerd Fonts icon layer. The
default branch, `dev/main`, contains the integrated customizations; `main` is
kept for synchronization with upstream.

## What is customized

- **Sarasa Term only**, in `SC`, `TC`, and `J` regional variants.
- Four styles per region: Regular, Italic, Bold, and Bold Italic.
- A reproducible custom Iosevka v34.7.0 Latin source based on `ss15` / IBM Plex
  Mono, with a tailed `l` and a serifed `1` for clearer `l` / `1` / `I`
  distinction.
- An optional Nerd Fonts v3.4.0 icon layer, merged as a post-processing step so
  the original Sarasa glyphs and hinting data remain intact.
- Automated checks for the SC/TC/J set, 1:2 Latin-to-CJK metrics, existing-glyph
  fidelity, icon cell width, naming, and release contents.

The normal release contains 24 hinted TTF files:

| Variant | Files | Installed family |
| --- | --- | --- |
| Without icons | `SarasaTerm{SC,TC,J}-{Style}.ttf` | `Sarasa Term SC/TC/J` |
| With Nerd icons | `SarasaTerm{SC,TC,J}-NF-{Style}.ttf` | `Sarasa Term SC/TC/J NF` |

The two variants use different family names and can be installed side by side.
See [Releases](https://github.com/r404r/Sarasa-Gothic/releases) for packaged
fonts, checksums, icon attribution, and platform-validation notes.

TTC packaging is under active research and development in this fork. It is not
part of the stable delivery described above until its validation work is
complete.

## Build

The upstream build requires Node.js 20 or newer, current AFDKO, and
`ttfautohint`. Install the JavaScript dependencies and build the configured TTF
set with:

```bash
npm install
npm run build ttf
```

The build output is written to `out/TTF`. A clean hinted CJK build can take
several hours.

The custom Latin recipe is kept in `iosevka-build/`. Nerd icon sources,
manifests, licenses, merge tools, and verification tools are under
`sources/nerd/` and `tools/nerd/`.

To assemble and validate a release without publishing it:

```bash
tools/release/make-release.sh --no-publish
```

Run `tools/release/make-release.sh --help` for prerequisites and release
options. Publishing requires an authenticated GitHub CLI session.

## Relationship to upstream

- `main` tracks `be5invis/Sarasa-Gothic` and is not used for personal feature
  development.
- `dev/main` is this fork's integration branch.
- `PR/*` branches contain isolated custom changes before they are integrated
  into `dev/main`.

Contributions intended for upstream should be based on an up-to-date `main`,
not `dev/main`, so this fork's product choices, bundled sources, and README do
not enter the upstream pull request. Before opening such a PR, verify its scope
with:

```bash
git diff upstream/main...HEAD
```

## License and attribution

Sarasa Gothic is licensed under the SIL Open Font License 1.1; see
[`LICENSE`](LICENSE). Nerd-enabled release artifacts include the applicable
third-party license and attribution bundle. Upstream project credit belongs to
the Sarasa Gothic, Iosevka, Inter, and Source Han Sans contributors.
