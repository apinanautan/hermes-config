# Branch Deduplication Workflow

## Problem
When sync creates multiple branches (master, config-sync, new-default, main — all at different commits), need to identify the correct one and consolidate to a single branch.

## When This Happens
- First push to new repo → `master` branch created
- Subsequent force-pushes to different branch names → multiple branches exist
- Pre-receive hook on protected branch blocks push → workaround creates new branch

## Decision Tree

```
1. List all remote branches with commit and file count:
   for b in $(git branch -r | grep -v HEAD); do
     echo -n "$b: "; git log origin/$b --oneline -1; echo -n "files: "; git ls-tree -r --name-only origin/$b | wc -l
   done

2. Identify target branch (most files + correct commit)

3. If target is NOT main:
   git push -f origin <best-sha>:refs/heads/main

4. If main has stale content:
   git push -f origin <correct-sha>:refs/heads/main

5. Delete all OTHER branches:
   git push origin --delete branch1 branch2 branch3

6. Rename local to main if needed:
   git branch -m old-name main

7. Prune stale remote refs:
   git remote prune origin

8. Verify:
   git branch -a
   git ls-remote --heads origin
```

## Key Metric: File Count

| Branch | Files | Notes |
|--------|-------|-------|
| new-default | 16 | ✓ Safe files only (after .gitignore cleanup) |
| config-sync | 5871 | ✗ Contains node/ (2.4GB binary) |
| main/master | 12 | ✗ Too few — hermes-agent, config-source excluded by mistake |

**Rule:** Highest file count isn't always best. Check what IS actually in the branch.

## Critical: .gitignore Errors

Common mistake that causes "only 12 files synced":
```
# WRONG — excludes entire folders
config-source/
hermes-agent/
skills/
scripts/
inventory/

# CORRECT — exclude only runtime junk inside them
hermes-agent/node_modules/
hermes-agent/__pycache__/
```

Safe folders to ALWAYS track:
```
scripts/        # auto-sync.sh, utilities
skills/         # skill definitions
inventory/      # Hermes inventory system
hermes-agent/   # Hermes agent core
config-source/  # Config source
checkpoints/    # Hermes checkpoint state
```

Runtime junk to ALWAYS exclude:
```
logs/
sessions/
cache/
audio_cache/
.env*
*.log
*.pid
*.lock
node_modules/
venv/
```

## Large Binary Warning

`node/` directory contains `node/bin/node` at 118MB+ — exceeds GitHub's 100MB limit → pre-receive hook rejection.

Always check before pushing large commits:
```bash
du -sh ~/.hermes/node/
du -sh ~/.hermes/hermes-agent/
```

If >100MB: add to .gitignore before commit.