# Publishing

The benchmark is developed inside the private `prometheus` monorepo and will be
published as its **own public repository**, split out with `git subtree split`
so the public history contains only the commits that touched this subdirectory.

## Why subtree split

- Keeps the public repo focused on the benchmark (no `community-agent`, no
  private tooling).
- **Preserves history**: every commit under `fhir-agent-benchmark/` is replayed
  onto the new root, so authorship and dates survive.
- Re-runnable: as work continues in the monorepo, the split can be re-done to
  update the public repo.

## One-time split

From the monorepo root (`prometheus/`):

```bash
# 1. Produce a branch whose root is fhir-agent-benchmark/ (history preserved)
git subtree split --prefix=fhir-agent-benchmark -b fhir-agent-benchmark-public

# 2. Create the empty public repo on GitHub first (no README/license), then:
git push git@github.com:<user>/fhir-agent-benchmark.git fhir-agent-benchmark-public:main
```

After the split, the public repo is fully self-contained — paths in
`benchmark_runner/` resolve relative to the package, so `validate-all` and
`pytest` work from the new root with no changes.

## Keeping it in sync (later)

Re-running the split rebuilds the branch from current history:

```bash
git subtree split --prefix=fhir-agent-benchmark -b fhir-agent-benchmark-public
git push git@github.com:<user>/fhir-agent-benchmark.git fhir-agent-benchmark-public:main
```

For ongoing two-way sync, `git subtree push`/`pull` (or the
[`git-filter-repo`](https://github.com/newren/git-filter-repo) tool for a one-off
clean extraction) are alternatives. For v0.1, a periodic one-way split is enough.

## Pre-publish checklist

- [ ] `python -m benchmark_runner.cli validate-all` passes
- [ ] `pytest -q` passes
- [ ] `LICENSE`, `README.md`, `CONTRIBUTING.md`, `CITATION.cff` present
- [ ] No PHI / real patient data (all cases synthetic)
- [ ] `CHANGELOG.md` updated with the released `taxonomy_version` / `scoring_version`
- [ ] Hugging Face dataset card prepared (mirrors `cases/`)
