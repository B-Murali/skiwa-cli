# skiwa

Skill wrangler: browse, install, and scaffold agent skills from a single
GitHub repo, using `gh` under the hood.

## Install

### From source (requires Python and `gh` on `PATH`)

```
pip install .
```

### Standalone binary (no Python or `gh` required)

Download the archive for your platform from the
[latest release](../../releases/latest), then:

**macOS / Linux**

```
tar -xzf skiwa-<target>.tar.gz
cd skiwa-<target>
chmod +x skiwa
./skiwa
```

macOS will flag the unsigned binary as unidentified on first run (it isn't
notarized). Clear the quarantine flag once:

```
xattr -d com.apple.quarantine ./skiwa
```

**Windows**

```
Expand-Archive skiwa-windows-x64.zip
cd skiwa-windows-x64
.\skiwa.exe
```

Each archive bundles a `gh` release binary as a fallback and includes its
license (`THIRD-PARTY-LICENSE-gh.txt`). If `gh` is already on your `PATH`,
skiwa uses that one instead — so your existing `gh auth login` session and
config keep working unchanged.

## Releasing a new build

Push a `v*` tag (e.g. `v0.1.0`). `.github/workflows/release.yml` builds
macOS (arm64 + x64), Linux (x64), and Windows (x64) binaries and attaches
them, plus a combined `SHA256SUMS.txt`, to the GitHub Release for that tag.
Trigger the workflow manually (`workflow_dispatch`) to build and inspect
artifacts without publishing a release.
