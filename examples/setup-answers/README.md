# Sample answers files

One complete answers file per purpose, in the format of [schemas/setup-answers.yaml](../../schemas/setup-answers.yaml). All names, addresses and paths are placeholders. Together they cover the four ways to build departments, a deferred answer, a planned repo, a protected repo, a roadmap board, each form of attribution, employer rules and a holding's policies repo.

- [job.yaml](job.yaml): purpose `job`; employer rules, where the remote lives, a deferred hq remote, no repos, attribution none.
- [product.yaml](product.yaml): purpose `product`; all four ways to build departments, a planned and protected repo, a roadmap board, attribution default.
- [startup.yaml](startup.yaml): purpose `startup`; a catalog entry that gains an ability, a custom department, a stricter and a looser gate, a deferred holding policy, your own attribution text.
- [company.yaml](company.yaml): purpose `company`, level company; a pinned holding policy, an own agent that replaces a catalog entry, an agent name set apart to resolve a clash, a protected repo.
- [holding.yaml](holding.yaml): purpose `company`, level holding; the policies repo path and ceilings, a deferred attribution answer.
- [personal.yaml](personal.yaml): purpose `personal`; health, money and paperwork, no repos and no roadmap, attribution none.

## Check a file

From the plugin folder:

```sh
python3 scripts/ci/check_setup_answers.py                      # the schema example and every file here
python3 scripts/ci/check_setup_answers.py --file my-answers.yaml
```

## Run a dry run

A dry run renders an hq from a file into the current directory, which must be empty, without git, commits, remotes or installs. Start Claude Code in a new empty folder (with the plugin installed) and run:

```
/ceo-of-agents:init-fleet /path/to/examples/setup-answers/product.yaml --dry-run
```

When it ends, check the result against the same file, from the plugin folder (the first argument is the folder of the dry run):

```sh
python3 scripts/check-dry-run.py <folder of the dry run> examples/setup-answers/product.yaml
```

The last line is `verdict: ok` or `verdict: N problem(s)`, with one line per problem above it.
