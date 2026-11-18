# Unreleased: setup answers file and dry run

Folded into the migration of the next release (see migrations/README.md). Issue: #58.

Plugin only: the setup wizard (`init-fleet`) can read all its answers from one file, in the format of `schemas/setup-answers.yaml`, and has a dry run that renders an hq from such a file without git, commits or installs. No file of an hq changes, and there is no schema change for `org.yaml` or `state.md`. An existing hq needs nothing.

## Summary line for the CEO

The setup wizard can now read all its answers from a file and has a dry run; nothing in your hq changes.

## Check after applying

`git status --short` shows nothing beyond the version bump the release adds.
