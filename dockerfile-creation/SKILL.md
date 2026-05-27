---
name: dockerfile-creation
description: 'Create, fix, or improve Dockerfiles. Use when writing a new Dockerfile, debugging a failed docker build, or improving an existing image. Ensures the image actually builds and runs before declaring it complete.'
---

# Dockerfile Creation

**Docker registry endpoint is always Docker Hub.**

A Dockerfile is not complete until it has been built and the resulting container verified to run correctly.

## Procedure

### 1. Write the Dockerfile

Apply the guidelines below, then create the file.

### 2. Build the image

```bash
docker build -t <image-name> .
```

If the build fails, fix the issue and rebuild. Do not skip this step.

### 3. Verify the container runs

Run a quick smoke test appropriate to the image:

- **CLI tools / entrypoint images**: run with `--help` or `--version`
  ```bash
  docker run --rm <image-name> --version
  ```
- **Servers / daemons**: start detached and check it stays up
  ```bash
  docker run -d --name test-container <image-name>
  docker ps | grep test-container
  docker rm -f test-container
  ```
- **One-shot scripts**: run and check exit code 0
  ```bash
  docker run --rm <image-name>
  echo "Exit: $?"
  ```

Only declare the Dockerfile complete once both the build and smoke test pass.

---

## Authoring Guidelines

### Network-dependent builds (downloading binaries/assets)

**Use `wget` instead of `curl` in Alpine images.**

- Busybox `wget` is built into Alpine — no extra package install needed.
- `curl` requires installing `libcurl` + dependencies and uses a libc-based DNS resolver that can fail to resolve GitHub CDN hostnames (`release-assets.githubusercontent.com`) inside Docker's bridge network, even when `wget` resolves them fine.
- If `curl` must be used and DNS fails during build, try `docker build --network=host`.

```dockerfile
# Preferred — no extra install needed
RUN wget -qO /tmp/tool.tar.gz "https://..." && \
    tar -xz -C /usr/local/bin -f /tmp/tool.tar.gz tool && \
    rm /tmp/tool.tar.gz

# Avoid piping download directly into tar — broken pipe errors when tar
# exits early after extracting a single named file while wget/curl is still streaming
# BAD:  wget -qO- "..." | tar -xz -C /usr/local/bin tool
# GOOD: download to temp file, then extract
```

### Version substitution in URLs

When a version tag (`v0.1.0`) is used in a path but the filename drops the `v` prefix (`tool_0.1.0_linux.tar.gz`), strip it with shell parameter expansion:

```dockerfile
RUN VERSION=$(wget -qO- "https://api.github.com/repos/owner/repo/releases/latest" \
        | grep '"tag_name"' \
        | sed 's/.*"tag_name": *"\([^"]*\)".*/\1/') && \
    wget -qO /tmp/tool.tar.gz \
        "https://github.com/owner/repo/releases/download/${VERSION}/tool_${VERSION#v}_linux_amd64.tar.gz"
#                                                                              ^^^^^^^^^^^
#                                                       strips leading 'v' for the filename segment
```

### Layer hygiene

- Combine `RUN` steps for related operations to avoid intermediate layers with leftover temp files.
- Clean up in the same `RUN` step that creates the mess:
  ```dockerfile
  RUN wget -qO /tmp/tool.tar.gz "..." && \
      tar -xz -C /usr/local/bin -f /tmp/tool.tar.gz tool && \
      rm /tmp/tool.tar.gz && \
      rm -rf /var/cache/apk/*
  ```

### Base image selection

- Prefer specific version tags (`alpine:3.20`) over `latest` for reproducible builds.
- For minimal images, start from `alpine` or `scratch`.
- Match the architecture to the target (e.g. `linux_amd64` vs `linux_arm64`).

### ENTRYPOINT vs CMD

- Use `ENTRYPOINT` for the primary executable (makes the container behave like the tool).
- Use `CMD` for default arguments that users are likely to override.
- Always use exec form (JSON array) to avoid shell signal-handling issues:
  ```dockerfile
  ENTRYPOINT ["tool"]
  CMD ["--help"]
  ```
