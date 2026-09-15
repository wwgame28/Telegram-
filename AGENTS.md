# ORLICA design agent instructions

This branch is the preserved ORLICA TATT site and its connected design stack.

## Design intelligence

Use **nextlevelbuilder/ui-ux-pro-max-skill** as the primary UI/UX design-intelligence source. Apply its accessibility, responsive layout, typography, interaction and anti-pattern checks before shipping visual changes.

Use **FinStep-AI/prd-writer-skill** when a request changes product requirements, information architecture, feature scope or user flow. Keep PRD work separate from production runtime code.

The other UI-UX-Pro-Max forks, localizations, benchmarks and demos visible in the source research are reference-only. Do not load multiple forks into production because they duplicate rules and can drift from the canonical source.

## Visual system

The requested visual language combines:

1. Asymmetrical graphic design layout.
2. Modular-grid editorial design.
3. Dynamic-composition graphic design.
4. Motion patterns inspired by Animos templates such as Iso Focus, Iso Cascade and orbit-style motion.

Animos is treated as a visual reference. Do not copy proprietary Animos source code or require Animos at runtime. Recreate motion locally with lightweight CSS/JavaScript.

## ORLICA constraints

- Preserve the monochrome editorial identity.
- Keep the existing Some Time Later vector headings.
- Preserve the current Sveta portrait asset and its facial appearance; do not replace, stylize or alter facial features without an explicit image-edit request.
- Mobile-first behavior matters: no horizontal overflow, no clipped labels, no animation that blocks taps or scrolling.
- Respect `prefers-reduced-motion`.
- Keep Telegram booking links functional.
- Avoid heavy runtime dependencies unless they materially improve the site.

## Runtime files

- `styles.css`, `mobile-fix.css`, `type-v8.css`: original ORLICA presentation layer.
- `script.js`: original interactions plus the design-stack loader.
- `design-stack.css`: asymmetry, modular grid, dynamic composition and motion presentation.
- `design-stack.js`: local Iso Focus / Iso Cascade / scroll composition behavior.
