# Git Workflow for s-CGCNN Project

**Version Control Strategy for s-CGCNN Development**

Author: Abdullah Hasan Dafa  
Project: s-CGCNN (Simplified CGCNN for AlGaAs Alloys)

---

## 📋 Overview

This document describes the Git branching strategy and workflow for s-CGCNN project development.

### **Branch Structure:**
- `master` - Stable releases only
- `v0.1.1`, `v0.2.0`, etc. - Version development branches
- `feature/*` - Individual feature branches (optional)

---

## 🌳 Branching Strategy

### **Main Branch: `master`**

**Purpose:** Production-ready code only  
**Protection:** Stable, tested releases

**Rules:**
- ✅ Only merge from version branches (e.g., `v0.1.1`)
- ✅ Each merge represents a complete, tested version
- ✅ Tagged with version numbers (e.g., `v0.1.1`)
- ❌ Never commit directly to master
- ❌ Never push untested code to master

**Content:**
- Stable, production-ready code
- Complete documentation
- All tests passing
- Ready for users to clone and use

---

### **Version Branches: `v0.1.1`, `v0.2.0`, etc.**

**Purpose:** Development of specific versions  
**Lifecycle:** Created for each new version, merged to master when complete

**Naming Convention:**
```
v<MAJOR>.<MINOR>.<PATCH>

Examples:
- v0.1.0  (initial release)
- v0.1.1  (patch release - bug fixes, minor features)
- v0.2.0  (minor release - new features)
- v1.0.0  (major release - stable)
```

**Rules:**
- ✅ Branch from master for new versions
- ✅ All development happens here
- ✅ Commit frequently with clear messages
- ✅ Merge to master only when version is complete
- ✅ Delete after successful merge to master (optional)

---

## 🚀 Workflow for Version 0.1.1

### **Step 1: Create Version Branch**

```bash
# Start from master
git checkout master
git pull origin master

# Create new version branch
git checkout -b v0.1.1

# Push to remote
git push -u origin v0.1.1
```

---

### **Step 2: Development on v0.1.1 Branch**

Work on all files for v0.1.1:

```bash
# Make sure you're on v0.1.1 branch
git checkout v0.1.1

# Stage all new/modified files
git add .

# Or stage specific files
git add config/config_v0.1.1.yaml
git add src/utils/constants.py
git add run_version_0.1.1.py

# Commit with descriptive message
git commit -m "feat: Add dual data source support (literature + MP-API)"

# Push to v0.1.1 branch
git push origin v0.1.1
```

**Commit Message Guidelines:**
```
feat: Add new feature
fix: Bug fix
docs: Documentation changes
refactor: Code refactoring
test: Add or update tests
chore: Maintenance tasks

Examples:
- feat: Add MP-API integration with band gap correction
- fix: Correct composition rounding for discrete values
- docs: Update README with dual mode usage examples
- test: Add tests for literature vs MP-API comparison
```

---

### **Step 3: Regular Commits During Development**

Commit frequently as you work:

```bash
# After creating core files (BATCH 1)
git add config/ src/ run_version_0.1.1.py
git commit -m "feat: Core infrastructure for v0.1.1 dual source"
git push origin v0.1.1

# After creating tests
git add tests/
git commit -m "test: Add comprehensive test suite for v0.1.1"
git push origin v0.1.1

# After creating documentation
git add README_v0.1.1.md CHANGELOG.md
git commit -m "docs: Complete documentation for v0.1.1"
git push origin v0.1.1

# After creating BATCH 2 files
git add src/utils/ notebooks/ examples/
git commit -m "feat: Add utilities, notebooks, and examples"
git push origin v0.1.1
```

---

### **Step 4: Testing Phase**

Before merging to master, ensure everything works:

```bash
# Run all tests
python tests/1.1\ Adding\ Interpolation\ Source\ Selection.py

# Check requirements
python check_requirements.py

# Test pipeline
python run_version_0.1.1.py --mode literature

# Test comparison mode
python run_comparison_mode.py

# If tests pass, commit final changes
git add .
git commit -m "test: All tests passing for v0.1.1"
git push origin v0.1.1
```

---

### **Step 5: Merge to Master (Complete Version)**

When v0.1.1 is complete and tested:

```bash
# Switch to master
git checkout master
git pull origin master

# Merge v0.1.1 into master
git merge v0.1.1 --no-ff -m "Release v0.1.1: Dual data source support"

# Tag the release
git tag -a v0.1.1 -m "Version 0.1.1 - Dual data source (literature + MP-API)"

# Push master and tags
git push origin master
git push origin v0.1.1  # Keep version branch for reference

# Push tags
git push origin --tags
```

**Result:**
- Master now has stable v0.1.1
- Version branch v0.1.1 preserved for reference
- Release tagged as v0.1.1

---

### **Step 6: Continue Development (v0.2.0)**

For next version:

```bash
# Start from master (which now has v0.1.1)
git checkout master
git pull origin master

# Create v0.2.0 branch
git checkout -b v0.2.0
git push -u origin v0.2.0

# Start developing v0.2.0 features...
```

---

## 📊 Branch Timeline Example

```
master:     v0.1.0 -----(merge)-----> v0.1.1 -----(merge)-----> v0.2.0
                           ↑                          ↑
v0.1.1:            [dev... dev... dev... test]       |
                                                      |
v0.2.0:                                      [dev... dev... dev... test]
```

---

## 🔄 Complete Git Command Cheatsheet

### **Initial Setup (One-time)**

```bash
# Configure Git (if not done)
git config --global user.name "Abdullah Hasan Dafa"
git config --global user.email "your.email@example.com"

# Clone repository
git clone https://github.com/hasandafa/s-cgcnn.git
cd s-cgcnn
```

---

### **Starting New Version**

```bash
# Create version branch
git checkout master
git pull origin master
git checkout -b v0.1.1
git push -u origin v0.1.1
```

---

### **Daily Development**

```bash
# Check status
git status

# See what changed
git diff

# Stage files
git add <file>              # Specific file
git add .                   # All files
git add -u                  # Updated files only

# Commit
git commit -m "message"

# Push to version branch
git push origin v0.1.1
```

---

### **Viewing History**

```bash
# View commit log
git log

# View compact log
git log --oneline

# View branch graph
git log --graph --oneline --all

# View file history
git log --follow <filename>
```

---

### **Undoing Changes**

```bash
# Discard changes in working directory
git checkout -- <file>

# Unstage file (keep changes)
git reset HEAD <file>

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1
```

---

### **Merging to Master**

```bash
# Switch to master
git checkout master
git pull origin master

# Merge version branch
git merge v0.1.1 --no-ff

# Tag release
git tag -a v0.1.1 -m "Version 0.1.1"

# Push everything
git push origin master
git push origin --tags
```

---

## 📝 Commit Message Standards

### **Format:**
```
<type>: <subject>

<optional body>

<optional footer>
```

### **Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation only
- `style` - Formatting, missing semicolons, etc.
- `refactor` - Code restructuring
- `test` - Adding tests
- `chore` - Maintenance

### **Examples:**

**Good commit messages:**
```bash
feat: Add MP-API data source with fallback to literature
fix: Correct band gap correction factor calculation
docs: Update README with comparison mode examples
test: Add unit tests for structure interpolation
refactor: Simplify property calculation logic
chore: Update dependencies in requirements.txt
```

**Bad commit messages:**
```bash
update files          # Too vague
fixed stuff           # No context
WIP                   # Work in progress, not descriptive
asdf                  # Meaningless
```

---

## 🏷️ Tagging Strategy

### **Version Tags:**

```bash
# Create annotated tag
git tag -a v0.1.1 -m "Version 0.1.1: Dual data source support"

# Push tag to remote
git push origin v0.1.1

# Push all tags
git push origin --tags

# List all tags
git tag -l

# Delete tag (if needed)
git tag -d v0.1.1
git push origin :refs/tags/v0.1.1
```

### **Tag Naming:**
- Use semantic versioning: `v<MAJOR>.<MINOR>.<PATCH>`
- `v0.1.1` - Patch release
- `v0.2.0` - Minor release
- `v1.0.0` - Major release

---

## 🚫 Common Mistakes to Avoid

### **❌ DON'T:**
1. Commit directly to master
2. Push broken code to any branch
3. Use vague commit messages
4. Forget to pull before pushing
5. Commit large binary files
6. Commit sensitive data (API keys, passwords)

### **✅ DO:**
1. Always work on version branches
2. Test before committing
3. Write clear commit messages
4. Pull frequently to avoid conflicts
5. Use .gitignore for generated files
6. Keep API keys in .gitignore files

---

## 📂 .gitignore Recommendations

Create/update `.gitignore`:

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
*.egg-info/

# Jupyter
.ipynb_checkpoints/
*.ipynb_checkpoints

# Data files (large)
data/
*.cif
*.json  # Except config files

# Logs
logs/
*.log

# API Keys
config/mp_api_key.txt

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
*.swp
*.swo

# Results (generated)
results/
*.png
*.pdf
```

---

## 🔍 Checking Branch Status

### **View all branches:**
```bash
# Local branches
git branch

# Remote branches
git branch -r

# All branches
git branch -a

# Current branch
git branch --show-current
```

### **Switch branches:**
```bash
# Switch to existing branch
git checkout v0.1.1

# Create and switch to new branch
git checkout -b v0.2.0
```

---

## 🆘 Troubleshooting

### **Problem: Merge conflict**

```bash
# During merge, Git will show conflicts
git merge v0.1.1

# Edit conflicted files manually
# Look for <<<<<<< HEAD markers

# After resolving conflicts
git add <resolved_files>
git commit -m "Merge v0.1.1 into master"
```

### **Problem: Pushed wrong commit**

```bash
# Undo last commit on remote (DANGEROUS!)
git reset --hard HEAD~1
git push origin v0.1.1 --force

# Better: Revert the commit (creates new commit)
git revert HEAD
git push origin v0.1.1
```

### **Problem: Forgot to create branch**

```bash
# Currently on master, made changes
git status  # Shows uncommitted changes

# Create branch now
git checkout -b v0.1.1

# Changes come with you to new branch
git add .
git commit -m "feat: Add new features"
git push -u origin v0.1.1
```

---

## 📊 Example: Complete v0.1.1 Workflow

```bash
# 1. Start new version
git checkout master
git pull origin master
git checkout -b v0.1.1
git push -u origin v0.1.1

# 2. Create BATCH 1 files
# ... create files ...
git add .
git commit -m "feat: Core v0.1.1 infrastructure (BATCH 1)"
git push origin v0.1.1

# 3. Create BATCH 2 files
# ... create files ...
git add .
git commit -m "feat: Utilities, notebooks, examples (BATCH 2)"
git push origin v0.1.1

# 4. Test everything
python check_requirements.py
python tests/1.1\ Adding\ Interpolation\ Source\ Selection.py
git add .
git commit -m "test: All tests passing"
git push origin v0.1.1

# 5. Update documentation
git add README_v0.1.1.md CHANGELOG.md
git commit -m "docs: Final documentation updates"
git push origin v0.1.1

# 6. Merge to master
git checkout master
git pull origin master
git merge v0.1.1 --no-ff -m "Release v0.1.1"
git tag -a v0.1.1 -m "Version 0.1.1: Dual data source support"
git push origin master
git push origin --tags

# 7. Done! v0.1.1 is now in master
```

---

## 🎓 Best Practices Summary

1. **Always branch** from master for new versions
2. **Commit often** with clear messages
3. **Test before merging** to master
4. **Tag releases** with version numbers
5. **Document changes** in CHANGELOG.md
6. **Use .gitignore** for generated/sensitive files
7. **Pull frequently** to stay updated
8. **Never commit** directly to master

---

## 📞 Need Help?

**Git Documentation:**
- https://git-scm.com/doc
- https://training.github.com/

**Common Commands:**
- `git status` - Check what's changed
- `git log` - View history
- `git diff` - See differences
- `git help <command>` - Get help

---

**Happy Coding with Proper Version Control!** 🚀

*Last updated: 2025-Q4 (v0.1.1)*  
*Author: Abdullah Hasan Dafa*