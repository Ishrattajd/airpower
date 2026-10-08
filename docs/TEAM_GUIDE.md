# Team Guide

## 1. One-time setup (every member)
1. Install **Python 3.12** (python.org). Python 3.14 works for Phase 1 but ML/optimiser packages may not have installers for it yet.
2. Install **Git for Windows** (git-scm.com) and **VS Code**.
3. Tell Git who you are (once):
   ```powershell
   git config --global user.name "Your Name"
   git config --global user.email "you@example.com"
   ```
4. Clone the repo, create your environment, check everything works:
   ```powershell
   git clone https://github.com/<owner>/airpower.git
   cd airpower
   py -3.12 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   pytest
   ```
   `pytest` must print "1 passed". If not, tell the lead before doing anything else.
   If PowerShell blocks the activate script, run once: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

## 2. Lead only: create the GitHub repo (first time)
1. github.com -> New repository -> name `airpower` -> **Private** -> do NOT tick README, .gitignore or licence -> Create.
2. In the project folder:
   ```powershell
   git init -b main
   git add .
   git status                       # check: no .venv, no data/raw, no passwords
   git commit -m "Phase 1 complete: data pipeline and frozen data v1"
   git remote add origin https://github.com/<owner>/airpower.git
   git push -u origin main
   git tag phase1-gate-passed
   git push --tags
   ```
3. Settings -> Collaborators -> add every teammate.

## 3. Daily routine
```powershell
git switch main
git pull                          # get the latest
git switch -c ml/rul-model        # new branch for your task (name: area/what)
# ... work, test ...
git add <files you changed>
git commit -m "Add RUL baseline model"
git push -u origin ml/rul-model   # then open a Pull Request on GitHub
```
- Never commit directly to `main` (except the lead's merges).
- A teammate or the lead reviews the Pull Request, then it is merged. Delete the branch afterwards.
- Commit small and often. Push at the end of every work session.
- Only change files in your own area (`src/ml`, `src/optimiser`, `src/dashboard`, `docs`). Need a change elsewhere? Ask the owner.

## 4. Rules that protect the project
1. **Never edit `data/frozen_v1/`.** `pytest` will fail if you do. If a real data problem is found, the lead decides, creates `frozen_v2`, and tells everyone.
2. **Read inputs only from `data/frozen_v1/`.** Write results only to `data/outputs/` and `models/`.
3. **Keep the file names and columns in the master plan's "File contracts"** table. If you must change one, tell everyone first.
4. **No secrets in Git** (passwords, API keys). Use environment variables.
5. **Do not commit files over 50 MB.**
6. Keep "SYNTHETIC DATA" visible in the dashboard and slides.
7. Before a Pull Request: run `pytest` and your own script from a clean start.

## 5. Who owns what
| Area | Owner |
|---|---|
| Plan, merging, final demo | Team lead |
| `src/data_pipeline`, data questions | Data engineer |
| `src/ml` | ML engineer |
| `src/optimiser` | Optimisation engineer |
| `src/dashboard` | Dashboard engineer |
| `docs`, slides, video | Documentation lead |

## 6. Useful commands
| Need | Command |
|---|---|
| See what changed | `git status` |
| Undo edits to one file (not yet committed) | `git restore <file>` |
| Switch branch | `git switch <name>` |
| Get teammates' work into your branch | `git switch main; git pull; git switch <yours>; git merge main` |
| Check frozen data | `python src/data_pipeline/11_freeze_data.py --verify` |
