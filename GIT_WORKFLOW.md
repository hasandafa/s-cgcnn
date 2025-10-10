# 🌳 Git Workflow Guide - s-CGCNN

Systematic branching strategy for version development.

---

## 📋 Branch Structure

```
master (main)          ← Always stable, reflects latest version
  │
  ├── version-0.1      ← Data Acquisition & Interpolation
  │
  ├── version-0.2      ← Structure Visualization
  │
  ├── version-0.3      ← Graph Building & Properties
  │
  ├── version-0.4      ← s-CGCNN Model & Training
  │
  ├── version-0.5      ← BS/DOS Prediction & Visualization
  │
  └── version-1.0      ← Device Recommendation (Stable Release)
```

---

## 🚀 Initial Setup (Version 0.1)

### 1. Create Repository on GitHub

```bash
# On GitHub: Create new repository 's-cgcnn'
# Check: Initialize with README (NO - we have our own)
# Add .gitignore: Python
# License: Your choice (e.g., MIT)
```

### 2. Initialize Local Repository

```bash
# Navigate to your s-cgcnn directory
cd s-cgcnn

# Initialize git
git init

# Add remote
git remote add origin https://github.com/hasandafa/s-cgcnn.git
```

### 3. Create Directory Structure with Placeholders

```bash
# Create .gitkeep files for empty directories
touch data/raw/.gitkeep
touch data/structures/cif/.gitkeep
touch data/structures/metadata/.gitkeep
touch data/graphs/.gitkeep
touch data/processed/.gitkeep
touch logs/.gitkeep
touch models/.gitkeep
touch results/figures/.gitkeep
touch results/models/.gitkeep
touch results/predictions/.gitkeep
touch results/recommendations/.gitkeep
touch notebooks/.gitkeep
touch tests/.gitkeep
```

### 4. Initial Commit to Master

```bash
# Add all files EXCEPT data/logs content
git add .
git add .gitignore
git add requirements.txt
git add README_v0.1.md
git add QUICKSTART.md
git add setup.py
git add src/
git add config/config_v0.1.yaml
git add "1. Data Acquisition and Structure Interpolation Testing.py"
git add run_version_0.1.py

# IMPORTANT: Do NOT add config/mp_api_key.txt
# Verify with:
git status

# Commit
git commit -m "Initial commit: Project structure and documentation"

# Push to master
git branch -M master
git push -u origin master
```

---

## 🔀 Version 0.1 Development

### 1. Create Version 0.1 Branch

```bash
# Create and switch to version-0.1 branch
git checkout -b version-0.1

# Verify you're on the right branch
git branch
# Output should show: * version-0.1
```

### 2. Development Workflow

```bash
# Make changes, test, iterate...

# Stage changes
git add src/data_acquisition/mp_fetcher.py
git add src/data_acquisition/structure_interpolator.py
git add src/utils/constants.py
git add src/utils/logger_config.py

# Commit with descriptive message
git commit -m "feat: Implement MP data fetcher and structure interpolator

- Add MPDataFetcher for Materials Project API integration
- Implement ordered supercell interpolation
- Add Vegard's Law with bowing parameters
- Include comprehensive property calculation
- Add logging and error handling"

# Push to remote
git push -u origin version-0.1
```

### 3. Testing & Validation

```bash
# Run tests
python "1. Data Acquisition and Structure Interpolation Testing.py"

# If tests pass, commit test results
git add logs/v0.1_test_report.json
git commit -m "test: Add v0.1 validation results"
git push
```

### 4. Merge to Master (When Complete)

```bash
# Switch to master
git checkout master

# Merge version-0.1
git merge version-0.1 --no-ff -m "Merge version-0.1: Complete data acquisition and interpolation

Version 0.1 Features:
- Materials Project API integration
- 41 AlGaAs structure generation
- Property interpolation with bowing
- Comprehensive testing suite"

# Push updated master
git push origin master

# Tag the version
git tag -a v0.1.0 -m "Version 0.1.0: Data Acquisition & Structure Interpolation"
git push origin v0.1.0
```

---

## 🔄 Subsequent Versions (0.2, 0.3, etc.)

### Starting Version 0.2

```bash
# Create from latest master
git checkout master
git pull origin master

# Create version-0.2 branch
git checkout -b version-0.2

# Start development...
```

### Incremental Commits

```bash
# Good commit message format:
# <type>: <short description>
#
# [optional body]
# [optional footer]

# Types:
# feat:     New feature
# fix:      Bug fix
# docs:     Documentation only
# style:    Formatting, missing semicolons, etc.
# refactor: Code restructuring
# test:     Adding tests
# chore:    Maintain

# Examples:
git commit -m "feat: Add crystal-toolkit visualization"
git commit -m "fix: Correct lattice parameter calculation"
git commit -m "docs: Update README with visualization guide"
git commit -m "test: Add visualization validation tests"
```

---

## 🔙 Rollback Strategy

### If Version 0.3 Has Issues

```bash
# Option 1: Start fresh from version-0.2
git checkout version-0.2
git checkout -b version-0.3-v2

# Option 2: Reset version-0.3 to version-0.2
git checkout version-0.3
git reset --hard version-0.2
# Force push (BE CAREFUL!)
git push --force origin version-0.3
```

### If Master Has Issues

```bash
# Revert to last good version tag
git checkout master
git reset --hard v0.2.0
git push --force origin master  # Use with EXTREME caution
```

---

## 📊 Branch Status Overview

```bash
# View all branches
git branch -a

# View branch history
git log --oneline --graph --all --decorate

# Compare branches
git diff version-0.1..version-0.2
```

---

## 🏷️ Tagging Strategy

```bash
# Version tags
v0.1.0  → First working version of 0.1
v0.1.1  → Bug fix for 0.1
v0.2.0  → First working version of 0.2
v1.0.0  → Stable release

# Create tag
git tag -a v0.1.0 -m "Version 0.1.0: Description"

# Push tags
git push origin v0.1.0
# or push all tags
git push --tags
```

---

## 🔒 .gitignore Best Practices

**Always exclude:**
- ✅ `config/mp_api_key.txt` (API keys)
- ✅ `data/raw/*.json` (Large data files)
- ✅ `data/structures/cif/*.cif` (Generated structures)
- ✅ `logs/*.log` (Log files)
- ✅ `models/*.pt` (Trained models)
- ✅ `__pycache__/` (Python cache)
- ✅ `venv/` (Virtual environment)

**Keep in Git:**
- ✅ `.gitkeep` files (directory structure)
- ✅ `config/config_*.yaml` (Configuration templates)
- ✅ Source code (`src/`)
- ✅ Documentation (`.md` files)
- ✅ Requirements (`requirements.txt`)
- ✅ Tests (`tests/`, `*.py` test files)

---

## 📝 Commit Message Template

Create `.gitmessage` template:

```bash
cat > .gitmessage << 'EOF'
# Type: feat|fix|docs|style|refactor|test|chore
# Scope: component affected (optional)
#
# Subject: imperative mood, max 50 chars
#
# Body: Explain WHAT and WHY (not HOW)
# - Bullet points okay
# - Reference issues: Closes #123
#
# Footer: Breaking changes, issues
EOF

# Set as default
git config commit.template .gitmessage
```

---

## 🚨 Emergency Procedures

### Accidentally Committed API Key

```bash
# Remove from last commit
git rm --cached config/mp_api_key.txt
git commit --amend

# If already pushed
git push --force

# Regenerate API key immediately!
```

### Accidentally Committed Large File

```bash
# Remove from git history (careful!)
git filter-branch --tree-filter 'rm -f data/large_file.dat' HEAD
git push --force
```

---

## ✅ Pre-Push Checklist

Before pushing to master:

- [ ] All tests pass
- [ ] No API keys in commits
- [ ] Documentation updated
- [ ] Changelog/version updated
- [ ] No merge conflicts
- [ ] Code linted/formatted

---

## 📞 Need Help?

```bash
# Show git help
git help <command>

# Show commit history
git log --oneline --graph

# Show changes
git diff

# Show branch info
git branch -vv
```

---

**Last Updated:** October 2025  
**Version:** 0.1.0