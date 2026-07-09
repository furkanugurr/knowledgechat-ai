# Git Branching

## Why Branches Are Useful

A Git branch is a movable name that points to a commit. Branches let developers
work on changes without immediately modifying the main line of development.
They are commonly used for features, bug fixes, and experiments.

Creating and switching to a branch can be done in one command:

```bash
git switch -c feature/example
```

New commits advance the current branch. Other branches keep pointing to their
existing commits until they are updated.

## Merging a Feature

Before merging, a developer normally reviews the diff and runs the relevant
tests. The branch is pushed to a remote repository and opened as a pull
request. After approval, merging combines the feature history with the target
branch.

```bash
git switch main
git pull --ff-only origin main
git merge feature/example
```

Teams may merge through their hosting platform instead of running the final
command locally. After a successful merge, the feature branch can be deleted
locally and remotely.

Branches reduce interference between tasks, but they do not replace small
commits, clear messages, reviews, or automated tests.
