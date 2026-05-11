# Embedded Git Repos — Submodule Problem

## Problem
When running `git add -A` inside ~/.hermes, nested `.git` directories (config-source, hermes-agent, etc.) cause git to add them as embedded git repositories with a warning:

```
warning: adding embedded git repository: config-source.old
hint: You've added another git repository inside your current repository.
hint: Clones of the outer repository will not contain the contents of
the embedded repository and will not know how to obtain it.
```

## Why It Happens
Any directory containing a `.git` folder inside the working tree gets added as a gitlink (submodule reference), not as regular files.

## How to Fix

### Before adding folders with nested .git:
```bash
# Remove nested .git directories
rm -rf config-source/.git
rm -rf config-source.old/.git
rm -rf hermes-agent/.git
rm -rf node/.git

# Then add normally
git add config-source config-source.old hermes-agent ...
```

### If already added as submodule:
```bash
# Remove from index
git rm --cached -r config-source config-source.old hermes-agent node

# Remove the nested .git directories
rm -rf config-source/.git config-source.old/.git hermes-agent/.git node/.git

# Now re-add
git add config-source config-source.old hermes-agent node
```

### Verify with:
```bash
git status --short | grep "^A " | head -20
# If you see "A  config-source/" without warning, it's a submodule
# If you see "A  config-source/AGENTS.md" it's regular files (good)
```

## When Nested .git Is Inside a Tracked Folder
If the nested .git was inside a folder already committed, you need to:
1. Remove from git index
2. Delete the nested .git folder
3. Reset the working tree
4. Re-add cleanly

```bash
git reset HEAD
git rm --cached -r config-source
rm -rf config-source/.git
git add config-source
```