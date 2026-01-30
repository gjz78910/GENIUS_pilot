# Dry Run Checklist - Two Participants

**Date:** ___________  
**Participant 1 (Manual):** ___________  
**Participant 2 (AI):** ___________

---

## BEFORE THE SESSION

### Equipment & Software Setup

- [ ] **One laptop/computer ready (used sequentially for both participants)**
  - [ ] Has VS Code installed
  - [ ] Has Python and conda installed
  - [ ] Has Git installed
  - [ ] Has internet connection

- [ ] **Screen recording software**
  - [ ] Install screen recording tool (e.g., OBS, QuickTime, or Zoom recording)
  - [ ] Test that it records screen clearly
  - [ ] Check audio settings (if needed for interviews later)
  - [ ] Make sure recording saves to a safe location

- [ ] **AI Assistant Setup (for Participant 2 only)**
  - [ ] Amazon Q Developer plugin installed in VS Code
  - [ ] Plugin is activated and working
  - [ ] Test that AI suggestions appear when typing code
  - [ ] Test that chat feature works

- [ ] **Codebase Setup**
  - [ ] Clone or copy the codebase to the laptop
  - [ ] Test that conda environment works: `conda activate genius_pilot`
  - [ ] Run demo to verify setup: `python -m src.demo`
  - [ ] Tag initial state: `git tag -a initial -m "Initial codebase state"` (if using Git)
  - [ ] **IMPORTANT:** After Participant 1 finishes, store their work and reset environment before Participant 2 starts

- [ ] **Environment Control (Before Each Participant)**
  - [ ] List background processes: `python SCRIPTS/list_background_processes.py`
  - [ ] Close browsers (unless participant needs them)
  - [ ] Close media players (Spotify, iTunes, etc.)
  - [ ] Close communication apps (Slack, Discord, etc.)
  - [ ] Close other IDEs (keep only VS Code)
  - [ ] Disable notifications
  - [ ] Verify minimal background processes running

- [ ] **Test Files Ready**
  - [ ] Benchmark files exist: `data/benchmarks/benchmark_small_*.json`
  - [ ] Test files exist: `tests/test_*.py`
  - [ ] Participant instructions ready:
    - [ ] `PARTICIPANT_INSTRUCTIONS_MANUAL.md` for Participant 1 (no AI)
    - [ ] `PARTICIPANT_INSTRUCTIONS_AI.md` for Participant 2 (with AI)

---

## START OF SESSION

### Welcome & Setup (15 minutes)

- [ ] **Greet both participants**
  - [ ] Explain this is a dry run/test
  - [ ] Explain one will code manually, one will use AI
  - [ ] Ask if they have questions

- [ ] **For Participant 1 (Manual Coding):**
  - [ ] Show them the laptop setup
  - [ ] Explain: "You can use Google, Stack Overflow, documentation - but NO AI tools"
  - [ ] Explain: "No ChatGPT, no AI chatbots, no AI in IDE"
  - [ ] Show them where PARTICIPANT_INSTRUCTIONS_MANUAL.md is
  - [ ] Start screen recording

- [ ] **For Participant 2 (AI Coding) - AFTER Participant 1 finishes:**
  - [ ] **Reset the environment:** Clean up Participant 1's work, restore fresh codebase
  - [ ] Show them the laptop setup
  - [ ] Show them the Q Developer AI plugin in VS Code
  - [ ] Explain: "You can use the AI assistant in VS Code"
  - [ ] Explain: "You can also use other AI tools if you want"
  - [ ] Show them where PARTICIPANT_INSTRUCTIONS_AI.md is
  - [ ] Start screen recording

- [ ] **Verify Setup Works**
  - [ ] Participant 1 runs: `python -m src.demo` (should see output)
  - [ ] After Participant 1 finishes, verify setup again for Participant 2: `python -m src.demo`
  - [ ] Both should see output (engineers, jobs, routes)
  - [ ] If errors, fix them before starting tasks

---

## DURING THE SESSION

### Task Assignment

- [ ] **Give both participants the same task**
  - [ ] Choose ONE task to test (recommend Task 2 or Task 3 - simpler)
  - [ ] Give them the task description from EXPERIMENT_DOCUMENTS/PARTICIPANT_INSTRUCTIONS_MANUAL.md or PARTICIPANT_INSTRUCTIONS_AI.md
  - [ ] Set a time limit (e.g., 30-60 minutes for dry run)
  - [ ] Tell them to start

### Monitor Participants (One at a Time)

- [ ] **While Participant 1 is working (Manual):**
  - [ ] Are they using search engines? (OK)
  - [ ] Are they using AI chatbots? (NOT OK - remind them)
  - [ ] Are they making progress?
  - [ ] Are they stuck? (Note what they're stuck on)

- [ ] **After Participant 1 finishes, reset environment, then:**
  - [ ] **While Participant 2 is working (AI):**
    - [ ] Are they using the AI assistant? (Check if plugin is being used)
    - [ ] Are they accepting/rejecting AI suggestions?
    - [ ] Are they making progress?
    - [ ] Are they stuck? (Note what they're stuck on)

- [ ] **Technical Issues to Watch For:**
  - [ ] Any errors in terminal? (Note them)
  - [ ] Tests failing? (Note which tests)
  - [ ] Code not running? (Note the error)
  - [ ] Screen recording still working? (Check periodically)

---

## END OF SESSION

### Stop Recording & Collect Data

- [ ] **Stop screen recordings**
  - [ ] Save recordings with clear names: `participant1_manual_DATE.mp4` and `participant2_ai_DATE.mp4`
  - [ ] Verify recordings are complete (not corrupted)

- [ ] **After Participant 1 finishes:**
  - [ ] Stop screen recording for Participant 1
  - [ ] Stop resource monitoring (Ctrl+C or kill process)
  - [ ] **STORE PARTICIPANT 1'S WORK (CRITICAL - do this first!):**
    - [ ] Run: `./SCRIPTS/store_participant_work.sh P001 SESSION1` (replace P001 with actual ID)
    - [ ] Verify backup was created: Check `DATA_COLLECTION/participant_backups/`
    - [ ] Verify state file exists: `DATA_COLLECTION/participant_state_P001_SESSION1.json`
    - [ ] Note: Participant work is now safely stored
  - [ ] **RESET ENVIRONMENT for Participant 2:**
    - [ ] Run: `./SCRIPTS/reset_environment.sh P001 SESSION1`
    - [ ] Verify demo still works: `python -m src.demo`
    - [ ] Verify all tests pass: `python -m unittest discover -s tests -p "test_*.py" -v`
    - [ ] Verify no Participant 1 code remains (check git status)
    - [ ] Make sure AI plugin is enabled (for Participant 2)

- [ ] **After Participant 2 finishes:**
  - [ ] Stop screen recording for Participant 2
  - [ ] Stop resource monitoring (Ctrl+C or kill process)
  - [ ] **STORE PARTICIPANT 2'S WORK (CRITICAL - do this first!):**
    - [ ] Run: `./SCRIPTS/store_participant_work.sh P002 SESSION1` (replace P002 with actual ID)
    - [ ] Verify backup was created: Check `DATA_COLLECTION/participant_backups/`
    - [ ] Verify state file exists: `DATA_COLLECTION/participant_state_P002_SESSION1.json`
    - [ ] Note: Participant work is now safely stored
  - [ ] Ensure participant data is anonymized before storage

- [ ] **Test Their Solutions (After Both Finish)**
  - [ ] **Restore Participant 1's work:**
    - [ ] Run: `./SCRIPTS/restore_participant_work.sh P001 SESSION1 --separate-dir`
    - [ ] Or switch to their branch: `git checkout participant-P001`
    - [ ] Run tests: `python -m unittest discover -s tests -p "test_*.py" -v`
    - [ ] Check success criteria: See `EXPERIMENT_DOCUMENTS/SUCCESS_CRITERIA.md`
    - [ ] Note which tests pass/fail
  - [ ] **Restore Participant 2's work:**
    - [ ] Run: `./SCRIPTS/restore_participant_work.sh P002 SESSION1 --separate-dir`
    - [ ] Or switch to their branch: `git checkout participant-P002`
    - [ ] Run tests: `python -m unittest discover -s tests -p "test_*.py" -v`
    - [ ] Check success criteria: See `EXPERIMENT_DOCUMENTS/SUCCESS_CRITERIA.md`
    - [ ] Note which tests pass/fail
  - [ ] **Compare solutions:**
    - [ ] Note differences in approach
    - [ ] Compare test results
    - [ ] Compare code quality (if Task 1, compare benchmark metrics)

---

## POST-SESSION CHECKS

### Verify What Was Recorded

- [ ] **Screen Recordings:**
  - [ ] Can you see the code clearly?
  - [ ] Can you see the terminal output?
  - [ ] Can you see AI suggestions (for Participant 2)?
  - [ ] Is the recording quality good enough?

- [ ] **Code Changes:**
  - [ ] Can you see what files were changed?
  - [ ] Can you see Git commits (if using Git)?
  - [ ] Can you run their code?

- [ ] **Terminal Outputs:**
  - [ ] Are terminal outputs visible in screen recording?
  - [ ] If not, did you capture them separately?

### Quick Feedback Session (Optional - 10 minutes)

- [ ] **Ask Participant 1 (Manual):**
  - [ ] "Was the task clear?"
  - [ ] "What was difficult?"
  - [ ] "Did you need any help?"
  - [ ] "Any technical issues?"

- [ ] **Ask Participant 2 (AI):**
  - [ ] "Was the AI assistant helpful?"
  - [ ] "Did it work as expected?"
  - [ ] "What was difficult?"
  - [ ] "Any technical issues?"

---

## THINGS TO CHECK AFTER DRY RUN

### Technical Issues

- [ ] **Screen Recording:**
  - [ ] Quality is good enough
  - [ ] Terminal is visible
  - [ ] Code is readable
  - [ ] Recording didn't crash or stop early

- [ ] **Environment Setup:**
  - [ ] Conda environment worked for both
  - [ ] Tests could run
  - [ ] No missing dependencies
  - [ ] Codebase was accessible

- [ ] **AI Assistant (Participant 2):**
  - [ ] Plugin worked correctly
  - [ ] Suggestions appeared
  - [ ] Chat feature worked (if used)
  - [ ] No crashes or errors

### Process Issues

- [ ] **Instructions:**
  - [ ] Were task descriptions clear?
  - [ ] Did participants understand what to do?
  - [ ] Were there confusing parts?

- [ ] **Time Management:**
  - [ ] Was the time limit appropriate?
  - [ ] Did participants finish or need more time?
  - [ ] How long did each participant take?

- [ ] **Data Collection:**
  - [ ] Did you capture all needed data?
  - [ ] Can you analyze what happened?
  - [ ] Are there gaps in what was recorded?
  - [ ] **Verify data separation:**
    - [ ] Run: `python SCRIPTS/verify_data_separation.py`
    - [ ] Check all files have participant IDs
    - [ ] Verify no cross-contamination
    - [ ] List participants: `python SCRIPTS/verify_data_separation.py --list-participants`

---

## NOTES SECTION

**Issues Found:**
- 

**What Worked Well:**
- 

**What Needs Fixing:**
- 

**Recommendations for Real Experiment:**
- 

---

## QUICK REFERENCE COMMANDS

**Test setup:**
```bash
conda activate genius_pilot
python -m src.demo
```

**Store/Reset workflow:**
```bash
# Store participant work (BEFORE reset!)
./SCRIPTS/store_participant_work.sh <PARTICIPANT_ID> <SESSION_ID>

# Reset environment (AFTER storing work!)
./SCRIPTS/reset_environment.sh <PARTICIPANT_ID> <SESSION_ID>

# Restore participant work (if needed)
./SCRIPTS/restore_participant_work.sh <PARTICIPANT_ID> <SESSION_ID>
./SCRIPTS/restore_participant_work.sh --list  # List available participants
```

**Run tests:**
```bash
python -m unittest tests.test_report_correctness -v
python -m unittest tests.test_data_loader -v
python -m unittest tests.test_benchmarks -v
python -m unittest discover -s tests -p "test_*.py" -v
```

**Verify data:**
```bash
# Verify data separation
python SCRIPTS/verify_data_separation.py
python SCRIPTS/verify_data_separation.py --list-participants
```

**Generate report:**
```bash
python -c "from src.features.report import generate_report; from src.scheduling.scheduler import Scheduler; from data.sample_data import engineers, jobs; from data.travel_matrix import travel_matrix; scheduler = Scheduler(engineers, jobs, travel_matrix); assignments, routes, unassigned = scheduler.create_schedule(); generate_report(engineers, assignments, routes, travel_matrix)"
```

**Load external data:**
```bash
python -c "from src.features.data_loader import load_data; engineers, jobs, travel_matrix = load_data('data/benchmarks/benchmark_small_01.json'); print(f'Loaded: {len(engineers)} engineers, {len(jobs)} jobs')"
```
