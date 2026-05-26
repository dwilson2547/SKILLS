---
name: gitignore-cli
description: 'Generate or update a .gitignore file for a project. Use when the user asks to add a gitignore, set up a gitignore, or when starting a new repo that needs one. Also use proactively when creating a new project that has no .gitignore yet.'
---

# gitignore-cli

Generates or appends to `.gitignore` using the `gitignore` CLI tool. Always assume the tool
is installed. If it is not found, see [INSTALL.md](./INSTALL.md).

## Usage

**Discover available templates:**
```bash
gitignore --list
```
Prints all available template names, one per line. Use this to find the right name before applying.

**Apply a template non-interactively:**
```bash
gitignore --quiet <template>
```
Creates `.gitignore` if absent; appends with a section header if one already exists.
Template name matching is case-insensitive.

**Apply multiple templates:**
```bash
gitignore --quiet Python
gitignore --quiet JetBrains
```
Run once per template — each appends cleanly.

## Workflow

1. Identify what the project is built with (language, framework, editor, OS)
2. Run `gitignore --list` to confirm the exact template names
3. Apply each relevant template with `gitignore --quiet <template>`
4. Verify `.gitignore` exists and looks correct

## Common Templates

`Go`, `Python`, `Node`, `React`, `Java`, `Rust`, `JetBrains`, `VisualStudioCode`, `macOS`, `Linux`, `Windows`

When in doubt, run `--list` — the source is the upstream GitHub gitignore project so coverage is comprehensive.
