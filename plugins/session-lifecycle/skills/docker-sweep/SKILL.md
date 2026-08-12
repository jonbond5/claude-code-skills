---
name: docker-sweep
description: Find Docker assets this session created that will never be used again — dangling images orphaned by a retag, one-off benchmark images, stopped throwaway containers, BuildKit cache from a one-off build — and report them with the exact narrow reclaim command. Reports by default; deletes only on explicit opt-in. Use at session end after building images or running throwaway containers, or when a partition is filling. Split out of /distill.
disable-model-invocation: true
allowed-tools: Bash Read
---

# /docker-sweep

Docker performs **no garbage collection by default.** Dangling images and BuildKit cache grow
unbounded until a partition fills. This skill makes session-created Docker junk visible before it
becomes that.

> *Real incident: a multi-arch buildx builder hoarded ~80G of cache over 5 weeks, and 38
> retag-orphaned `<none>` images held ~70G — together ~90% of a 456G root partition. `docker system
> df` was **blind** to the 80G because it lived in a volume attached to a running buildkit container.
> Nothing scheduled ever pruned it.*

**Assume the daemon is shared.** Other projects' containers may be live on the same host, and named
volumes routinely hold real databases — so a pattern-matched delete can take out something nobody
told you about. Check your own working agreement for a destructive-op rule before deleting anything.

## When to run

After a session that ran `docker build` / `compose build` / `buildx build`, started a throwaway
container, or tagged an image for a one-off. **If the session touched no Docker assets, say so and
stop** — that's the common case.

## Phase 1 — Enumerate what THIS session created

Walk the transcript, then confirm against live `docker` state. For each asset, classify:

- **PRUNABLE (session-transient)** — will not be used outside this session: a `<none>` image orphaned
  by a retag *this session* did; an image built ONLY to run a one-off benchmark/experiment/test (not
  part of a persistent stack); a stopped throwaway container; build cache from a one-off build.
- **KEEP (persistent)** — backs a running container, is referenced by a committed compose service or
  by a registry/engine entry the session added on purpose, or is shared inventory (base images,
  model-server images, DB volumes). **When unsure, KEEP.**

## Phase 2 — Verify before listing (name-matching is not proof)

For each candidate, confirm it is genuinely session-transient and unreferenced:

```bash
docker ps -a --format '{{.ID}} {{.Image}} {{.Status}} {{.Names}}'   # nothing running uses it
docker images --filter dangling=true --format '{{.ID}} {{.Size}} {{.CreatedSince}}'
```

Then check the project's compose files and any arbiter/engine registry the session touched. **An image
sharing a name with a stack image is NOT automatically prunable.**

**The blind spot:** a `docker-container` buildx builder's cache is masked from `docker system df`, and
builders created under a user account are invisible to `sudo docker buildx ls` (they live in
`~/.docker/buildx/`). Check explicitly, as the owning user:

```bash
docker buildx ls
docker buildx du --builder <each-builder>
```

Also worth a look when a partition is tight — `du` as a non-root user silently undercounts root-owned
trees, so a `df`-vs-`du` gap points at `/var/lib/docker`:

```bash
df -h /var/lib/docker && sudo du -sh /var/lib/docker && sudo lsof -nP +L1 | head
```

## Phase 3 — Report

Default output is a **list, not a deletion**:

```
/docker-sweep
  Prunable:  N asset(s), ~XG
    <asset>  <size>  <why session-transient>  ->  <exact narrow command>
  Kept:      M asset(s)  (one-line reason each)
  Builders:  <name>: <cache size>   [or: none beyond default]
  Disk:      <df used> vs <sudo du total>  [flag a gap]

  Recommendation: <one line>
```

## Guardrails (non-negotiable)

- **Report by default; confirm before deleting** — the prove-it-is-disposable rule in
  `~/.claude/CLAUDE.md` governs, and here that means only assets that passed Phase 2. The
  Docker-specific never-touch list is the rest of this section.
- **NEVER `docker image prune -a`** — it deletes intentional untagged-but-wanted inventory (e.g. large
  model-server images not currently backing a container). Use dangling-only `docker image prune -f`,
  `docker rmi <specific-id>`, or `docker buildx prune --keep-storage <N>g`.
- **NEVER `docker system prune` or `docker volume prune`** — each reaches every project on this shared
  daemon.
- **Never** prune an image backing a running container, a DB volume, or a registered engine image,
  even if it looks idle.
- **Ground truth only.** Verify size and reference state from live `docker` output this session, never
  from a subagent's claim.

## Prevention worth mentioning once

If your host keeps refilling: cap the builder with `[worker.oci] gc=true, gckeepstorage="<N>GB"` in its
buildkitd config, remove dead builders (`docker buildx rm`), and schedule a periodic dangling-only
prune. Offer this; don't configure it unasked.
