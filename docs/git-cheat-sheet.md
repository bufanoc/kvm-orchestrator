# Git Workflow Cheat Sheet (Solo Dev)

## Daily loop
```bash
git checkout main
git pull origin main     # sync local with GitHub
# ...do work...
git add -A               # stage changes
git commit -m "msg"      # save point
git push origin main     # publish to GitHub

# Feature branch --> PR (preferred when practicing reviews

git checkout -b feature/my-change
# ...do work...
git add -A
git commit -m "my change"
git push -u origin feature/my-change
# Open PR on GitHub → Review → Merge
git checkout main
git pull origin main

# Fix last commit message (before pushing)

git commit --amend -m "better message"

# See what changed

git status
git diff                 # unstaged
git diff --staged        # staged
git log --oneline --graph --decorate

# Undo (safe)

git restore <file>       # drop unstaged edits in file
git restore --staged <file>   # unstage, keep changes
git checkout main && git pull # fix "diverged" by updating

#Merge conflicts (fast path)

# after git pull reports conflicts
# edit files to resolve >>>>>> <<<<<< markers
git add -A
git commit               # completes the merge


Commit it:
```bash
git add docs/git-cheat-sheet.md
git commit -m "docs: add Git workflow cheat sheet"
git push

