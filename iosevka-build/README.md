# Iosevka Latin source build recipe

The four `sources/IosevkaNTerm/IosevkaNTerm-{Regular,Italic,Bold,BoldItalic}.ttf`
Latin sources in this branch are self-built to improve l/1 legibility
(l tailed, ss15 / IBM Plex Mono base style).

- Iosevka pinned tag: **v34.7.0**
- Build plan: `private-build-plans.toml` (buildPlans.IosevkaCustom)
- Reproduce: clone be5invis/Iosevka at v34.7.0, drop in this toml as
  `private-build-plans.toml`, `npm ci`, build the 4 styles, rename outputs
  to `IosevkaNTerm-<Style>.ttf`.
