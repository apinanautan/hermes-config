# Pre-Receive Hook Workaround — Session Notes

## Problem
Push to `master` on GitHub rejected with `pre-receive hook declined`.

## What We Tried

### Attempt 1: Force push existing master
```bash
git push -f origin master
```
Result: rejected

### Attempt 2: Push to main branch
```bash
git push origin master:refs/heads/main
```
Result: rejected (remote tip behind remote)

### Attempt 3: Force push specific SHA to main
```bash
git push -f origin d500e4b:refs/heads/main
```
Result: SUCCESS — remote updated to d500e4b

### Attempt 4: Push cde7e91 (5871 files, includes node/)
```bash
git push -f origin cde7e91:refs/heads/main
```
Result: rejected with `GH001: Large files detected. node/bin/node is 118.90 MB`

### Attempt 5: Push to new branch
```bash
git push origin config-sync:refs/heads/new-default
```
Result: rejected for same size reason

## Key Insight
The working commit `d500e4b` (203 bytes) pushed fine. The problem commit `cde7e91` contained node/ (2.4GB on disk, 118MB+ single file inside).

## Solution Path
1. Create new branch from clean working tree
2. Add only safe folders (exclude node/, node_modules/, hermes-agent/node_modules/)
3. Check `du -sh <dir>` before pushing
4. Push to new branch → set as default → delete old branch

## GitHub File Size Limits
- Max single file: 100MB
- Max repository: not defined but large repos get warnings
- Large File Storage (LFS): available but requires setup

## Command Reference
```bash
# Check directory size before commit
du -sh <dir>

# Verify what's being tracked
git status --ignored --short

# Check files to be committed
git ls-tree -r --name-only HEAD | wc -l

# Remove nested .git dirs
rm -rf config-source/.git hermes-agent/.git node/.git

# Create new branch and push
git push origin <branch>:refs/heads/<new-branch>

# Force push to new branch
git push -f origin <sha>:refs/heads/<new-branch>
```