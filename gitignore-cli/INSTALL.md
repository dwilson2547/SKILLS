# Installing gitignore-cli

Pre-built binaries for all platforms are published automatically on each release via GitHub Actions.

**Download a binary:**
https://github.com/dwilson2547/gitignore-cli/releases/latest

Download the binary for your OS/architecture, rename it to `gitignore`, and place it on your PATH.

**Via Go:**
```bash
go install github.com/dwilson2547/gitignore-cli@latest
```

**From source:**
```bash
git clone https://github.com/dwilson2547/gitignore-cli
cd gitignore-cli
go build -o gitignore .
mv gitignore /usr/local/bin/
```

After install, verify with:
```bash
gitignore --version
```
