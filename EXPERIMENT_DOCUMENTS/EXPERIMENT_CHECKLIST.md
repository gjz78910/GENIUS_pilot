# Experiment Preparation Checklist

**Date:** ___________
**Participant ID:** ___________
**Session Type:** [ ] Manual Coding  [ ] AI-Assisted Coding

---

## 0. Get Your Participant ID

- [ ] You should have been given a unique participant ID (e.g. `KCL001`, `BT001`)
- [ ] If you have not received one, **ask the experiment organiser before continuing**
- [ ] Use this ID exactly (same capitalisation) every time `<ID>` appears in this checklist

---

## 1. Clone the Repo and Create Your Branch

- [ ] Clone and enter the repo:
  ```bash
  git clone https://github.com/gjz78910/GENIUS_pilot.git
  cd GENIUS_pilot
  ```
- [ ] Create and switch to your own branch (replace `<ID>` with your participant ID, e.g. `KCL001`):
  ```bash
  git checkout -b participant/<ID>
  ```

---

## 2. Set Up the Environment

- [ ] If conda is not installed, install Miniconda:
  - Download from: https://docs.conda.io/en/latest/miniconda.html
  - Run the installer, accept defaults, **restart the terminal**
- [ ] `conda env create -f environment.yml`
- [ ] `conda activate genius_pilot`
- [ ] Verify: `python -m src.demo` — should print engineers, jobs, and routes

---

## 3. Fill the Pre-Experiment Survey

- [ ] Open `EXPERIMENT_DOCUMENTS/Pre_Experiment_Survey.md` in VS Code
- [ ] Put an "x" into the checkbox as selection, e.g.: [x]
- [ ] Save the file (Ctrl+S / Cmd+S)

---

## 4. Start Data Collection and Screen Recording

- [ ] Collect system info (replace `<ID>` with your participant ID, e.g. `KCL001`):
  ```bash
  python SCRIPTS/collect_system_info.py --participant-id <ID>
  ```
- [ ] Open a **new terminal** and start resource monitoring (replace `<ID>`, then leave it running):
  ```bash
  conda activate genius_pilot
  python SCRIPTS/monitor_resources.py --participant-id <ID> -i 60
  ```
- [ ] **Start screen recording** (record the full screen)

---

## 5. Run the Experiment

- [ ] Open `EXPERIMENT_DOCUMENTS/PARTICIPANT_INSTRUCTIONS.md` and follow the instructions
- [ ] Time limit: **2 hours**

---

## 6. Submit Completed Tasks

- [ ] Fill the post-experiment survey `EXPERIMENT_DOCUMENTS/Post_Experiment_Survey.md`
- [ ] Stage and push everything (replace `<ID>`):
  ```bash
  git add .
  git commit -m "Final submission <ID>"
  git push -u origin participant/<ID>
  ```
- [ ] **Stop screen recording**

---

## 7. Wrap Up 

- [ ] Stop resource monitoring: **Ctrl+C** in the monitor terminal
- [ ] Upload the screen recording video to the shared online drive: https://drive.google.com/drive/folders/1gQKB43GOSu1eiLllzqrSEVvJ_FZWbah9?usp=drive_link
- [ ] 🎉 Experiment complete! Thank you for participating! 🙌
