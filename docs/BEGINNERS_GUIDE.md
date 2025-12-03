# NoDupeLabs: Beginner's Guide

Welcome! This guide is written for someone who has never used this program before. It will walk you through setting up NoDupeLabs, scanning your files, and safely removing duplicates.

## 1. Prerequisites (What you need)

Before you start, you need a computer (Linux, macOS, or Windows) with a terminal (command prompt) and **Python 3.8 or newer** installed.

### How to check if you have Python:
1.  Open your terminal (Terminal on macOS/Linux, PowerShell or Command Prompt on Windows).
2.  Type the following command and press Enter:
    ```bash
    python3 --version
    ```
    *If that doesn't work, try `python --version`.*
3.  If you see something like `Python 3.10.12`, you are ready! If you get an error, you need to install Python from [python.org](https://www.python.org/).

---

## 2. Installation (Getting the program ready)

We need to download the code and tell your computer how to run it.

1.  **Download the code**:
    If you have `git` installed, run:
    ```bash
    git clone https://github.com/allaunthefox/NoDupeLabs.git
    cd NoDupeLabs
    ```
    *Alternatively, you can download the ZIP file from GitHub, unzip it, and open your terminal in that folder.*

2.  **Install the program**:
    Run this command to install NoDupeLabs and its dependencies:
    ```bash
    pip install -e .
    ```
    *(Note: On some systems, you might need to use `pip3` instead of `pip`)*.

---

## 3. Your First Scan (Cataloging your files)

The first step is to let NoDupeLabs look at your files. It will create a "fingerprint" (hash) for every file to see if they are identical, even if they have different names.

**Scenario**: You have a folder called `MyPhotos` that you want to check.

1.  Run the scan command:
    ```bash
    python3 -m nodupe.cli scan --root /path/to/MyPhotos
    ```
    *(Replace `/path/to/MyPhotos` with the actual location of your folder).*

2.  **What happens next?**
    *   You will see a progress bar as it reads your files.
    *   It creates a small file called `meta.json` inside every folder it scans. This file contains the catalog information.
    *   It saves a master database to `output/index.db`.

---

## 4. Finding Duplicates (Creating a Plan)

Now that the program knows about your files, ask it to find the duplicates.

1.  Run the plan command:
    ```bash
    python3 -m nodupe.cli plan --out my_cleanup_plan.csv
    ```

2.  **Review the Plan**:
    *   This creates a file named `my_cleanup_plan.csv`.
    *   **Open this file** in Excel, LibreOffice, or a text editor.
    *   It lists all the files that are duplicates and marks which ones will be moved/deleted (`DELETE`) and which one will be kept (`KEEP`).
    *   **Important**: If you don't like the plan, you can just delete the CSV file and nothing changes.

---

## 5. Removing Duplicates (Applying the Plan)

If you are happy with the plan, you can tell NoDupeLabs to execute it.

**Safety First**: By default, NoDupeLabs does **not** delete files. It moves them to a hidden folder called `.nodupe_duplicates` so you can recover them if needed.

1.  Run the apply command:
    ```bash
    python3 -m nodupe.cli apply --plan my_cleanup_plan.csv
    ```

2.  **What happens?**
    *   The program reads your CSV plan.
    *   It moves the duplicate files out of your way.
    *   It creates a "Checkpoint" file in `output/checkpoints/`. This is your "Undo" button.

---

## 6. Oops! (How to Undo)

If you realize you made a mistake or the program moved a file you wanted to keep, you can undo the entire operation.

1.  Find your checkpoint file:
    Look in the `output/checkpoints/` folder. You will see a file like `checkpoint_20251202_120000.json`.

2.  Run the rollback command:
    ```bash
    python3 -m nodupe.cli rollback --checkpoint output/checkpoints/checkpoint_20251202_120000.json
    ```
    *(Replace the filename with the one you found).*

3.  **Result**: All files are moved back to their original locations.

---

## 7. Advanced Tips

*   **Network Drives**: If you are scanning a network drive that might disconnect, don't worry. The scanner is smart enough to pause or skip errors without crashing.
*   **Configuration**: There is a file called `nodupe.yml` created after your first run. You can open it with a text editor to change settings (like ignoring certain folders).

---

**Need Help?**
If you get stuck, try running `python3 -m nodupe.cli --help` to see a list of available commands.
