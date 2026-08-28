# brand.json — the schema, not the values

The brand file is **customer-private and never lives in this repo.** The skill reads a
path; it does not carry a palette. Everything below is schema plus an obviously
invented worked example.

Keeping the values out of the skill is what makes the skill reusable across stores,
lines and seasons. It is also what stops an agent inventing a palette when the file is
missing — a skill with no default brand has nothing to fall back to, which is the
correct behaviour.

## Shape

```jsonc
{
  "brand": {
    "name": "Example Grocer",
    "palette": {
      // Every colour carries a role. A hex with no role invites an agent to use it
      // wherever it likes, which is how a secondary becomes a background.
      "primary":    { "hex": "#B4123A", "role": "price chip fill, logo lockup" },
      "secondary":  { "hex": "#F4E7D3", "role": "backdrop only" },
      "accent":     { "hex": "#1F7A3D", "role": "fresh/seasonal badge, never type" },
      "type":       { "hex": "#141414", "role": "all body copy" }
    },
    "logo": {
      // HTTPS URLs. The composite stage fetches these; it does not redraw them.
      "lockup_light": "https://cdn.example/brand/lockup-light.png",
      "lockup_dark":  "https://cdn.example/brand/lockup-dark.png",
      "min_width_px": 180,
      "clearspace_ratio": 0.5    // multiples of lockup height on every side
    },
    "typography": {
      "price_face": "https://cdn.example/brand/Grocer-Bold.woff2",
      "body_face":  "https://cdn.example/brand/Grocer-Regular.woff2"
    }
  },

  "price": {
    // The price is composited, never generated. These fields drive the overlay.
    "format": "£{major}.{minor}",
    "chip": { "fill": "primary", "text": "#FFFFFF", "corner_radius_px": 8 },
    "position": "bottom-right",
    "margin_ratio": 0.06,        // of the shorter edge
    "min_height_ratio": 0.09,    // QC gate fails below this
    "source": "required"         // "required" | "optional" — required means no price,
                                 // no asset, and the row is blocked at finish
  },

  "products": {
    // Keyed by SKU. reference_url is the locked product shot; it is never re-described
    // in a prompt, only passed as an image input.
    "STRAW-500G": {
      "display_name": "Strawberries 500g",
      "reference_url": "https://cdn.example/products/straw-500g.jpg",
      "price": { "major": 2, "minor": 49 },
      "claims": ["British", "Class 1"]   // rendered as copy, never invented
    }
  },

  "placements": {
    // The QC gate checks produced assets against these exactly.
    "feed_1x1":   { "aspect": "square_1_1",     "px": [1080, 1080], "meta": "feed" },
    "story_9x16": { "aspect": "portrait_9_16",  "px": [1080, 1920], "meta": "story" },
    "feed_4x5":   { "aspect": "portrait_4_5",   "px": [1080, 1350], "meta": "feed" }
  },
  "default_placements": ["feed_1x1", "feed_4x5", "story_9x16"],

  "flora": {
    "workspace_id": "ws_…",
    // The treatment. Authored once in FLORA's UI; the agent supplies inputs and cannot
    // rewrite the middle of it. This is the single strongest brand-control lever.
    "technique_id": "tec_…",
    // Only used when no technique fits. A model here means the brand is being carried
    // by prose again — treat it as a gap to close, not a configuration.
    "fallback_model": "t2i-flux-2-klein-4b"
  },

  "destinations": {
    "drive_folder_id": "1AbC…",
    "supabase_bucket": "campaign-assets",
    "supabase_prefix": "{campaign}/{asset_key}",
    "meta_ad_account_id": "act_…"
  }
}
```

## Rules for the agent

- **Missing file, missing brand, stop.** Never infer a palette from the campaign
  description, and never carry over a brand from an earlier conversation.
- **Roles are binding.** A colour may only be used for its stated role. `accent` marked
  "never type" means never type, including in a badge the model wanted to add.
- **Claims are quoted, not generated.** `claims` on a product is the complete list of
  what may be said about it. Adding "sweetest of the season" is a regulatory problem,
  not a creative flourish.
- **`price.source: "required"` blocks the row.** No price, no asset. Do not ship a frame
  with a placeholder and fix it later — a placeholder that reaches Meta is worse than a
  missing asset, because a paused ad looks finished.
- **Placements are exact.** A near-miss aspect ratio fails the gate. Meta will crop
  silently and the crop is where the price lives.

## Palette checking

The QC gate can only check what is structural. A workable check: sample the finished
frame, quantise, and assert that the dominant non-neutral colours fall within a
tolerance of the declared palette.

```
TODO(measure)  tolerance in CIEDE2000 that passes a correct frame and fails a drifted
               one. Record the pass and fail examples that set it.
TODO(measure)  false-positive rate on product photography — fruit is saturated and
               red strawberries against a #B4123A primary may be indistinguishable
               to a naive dominant-colour check.
```

This check catches gross drift — a backdrop that came back blue. It does not catch a
subtly wrong red, and it must not be reported as if it did.
