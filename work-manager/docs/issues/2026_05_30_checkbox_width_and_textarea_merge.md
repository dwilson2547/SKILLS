# Global input CSS rule expands checkboxes to full width and loses textarea-specific properties

**Date:** 2026-05-30  
**Component:** `ui/index.html` — CSS `input, select, textarea` rule  
**Severity:** Medium — cosmetic breakage; "Show archived" checkbox rendered as a large dark square,
and textarea elements lost their `min-height` and `resize` properties

---

## Observed symptom

After adding a "Show archived" checkbox to the Projects sidebar, the checkbox rendered as an
oversized dark block (full container width, standard input height) rather than a small inline
tickbox. Additionally, `<textarea>` elements in the UI had lost their `min-height: 120px` and
`resize: vertical` styling, making all text areas small and non-resizable.

---

## Root cause

### Single CSS selector covering all input types including checkboxes

The stylesheet uses a combined selector:

```css
input, select, textarea {
  width: 100%;
  ...
}
```

This rule applies `width: 100%` to every `<input>` regardless of type. Checkboxes (`type=checkbox`)
and radio buttons (`type=radio`) should never receive `width: 100%` as it expands them to fill
their container.

### Textarea-specific properties merged into shared rule during an edit

While converting the input background from a hardcoded `#fff` to `var(--surface)` for dark mode, the
edit accidentally merged `min-height: 120px; resize: vertical;` (which belonged in a separate
`textarea { }` block) into the shared `input, select, textarea { }` block. The standalone `textarea`
rule was lost, meaning all text inputs would receive the textarea sizing.

---

## Troubleshooting steps taken

1. **Took a Playwright screenshot** — "Show archived" checkbox appeared as a large dark square in
   the Projects sidebar, confirming the rendering regression.

2. **Inspected the DOM** — `document.querySelectorAll('input[type=checkbox]')` returned no results
   from within the `aside`, then after hard-reload the checkbox element was found and confirmed to
   have `width: 100%` applied via the shared input rule.

3. **Reviewed the CSS** — found `input, select, textarea { ... min-height: 120px; resize: vertical; }`
   confirming both issues: checkbox inclusion and merged textarea properties.

---

## Fix

### `ui/index.html` — Exclude checkbox and radio from the shared input rule; restore textarea block

Split the rule to exclude checkbox and radio inputs, and restore `textarea` as a separate block:

```css
/* Before */
input, select, textarea {
  width: 100%;
  border: 1px solid var(--border);
  border-radius: 0.7rem;
  background: var(--surface);
  color: var(--text);
  padding: 0.7rem 0.8rem;
  min-height: 120px;
  resize: vertical;
}

/* After */
input:not([type=checkbox]):not([type=radio]), select, textarea {
  width: 100%;
  border: 1px solid var(--border);
  border-radius: 0.7rem;
  background: var(--surface);
  color: var(--text);
  padding: 0.7rem 0.8rem;
}
textarea {
  min-height: 120px;
  resize: vertical;
}
```

---

## Files changed

- `ui/index.html` — CSS rule for `input, select, textarea`; restored separate `textarea` rule
