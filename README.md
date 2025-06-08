# Project: BPWatcher (Background GUI Automation Bot)

## Purpose

Automate interaction with the Best Practice (BP) Windows application to extract simple patient contact information and send it to a server, all without user awareness or UI.

## Core Workflow

1. **Startup**

   * Run automatically in the background at system boot via Windows Task Scheduler.
   * Must run silently (no UI, no tray, no visible window).

2. **Login**

   * Launch Best Practice executable.
   * Wait for login screen.
   * Simulate username/password entry and submit login.

3. **Navigate to Data**

   * After login, navigate to the "Patient List" section.
   * Optionally navigate to other known screens where patient contact info may appear.

4. **Data Capture**

   * Take a screenshot of the defined screen region where contact information appears.
   * Apply OCR to extract:

     * First Name
     * Last Name
     * Mobile / Home / Work Phone

5. **Sync**

   * Send the structured data (JSON) to a configured HTTPS endpoint.
   * Optionally log activity to a local file.

6. **Repeat**

   * Wait for a configured interval (e.g., 2 hours).
   * Repeat the full process silently.

## Technology Stack

* **Language**: Python
* **GUI Automation**: `pyautogui`, `pywinauto`, `pygetwindow`
* **OCR**: `pytesseract` + `Pillow`
* **Task Scheduling**: Windows Task Scheduler
* **Networking**: `requests`
* **Packaging**: `pyinstaller` (`--noconsole` for stealth)

## Security & Privacy

* Only extracts basic contact info (name + phone number)
* Does not access or store any clinical, birthdate, or Medicare data
* Credentials handled securely via `.env` or obfuscated script variables

## Installation Notes

* Convert Python script to `.exe` using PyInstaller with `--noconsole`
* Schedule task to run silently on startup with highest privileges
* Ensure Tesseract OCR and all dependencies are included in packaging or preinstalled

## AI Guidance

Cursor AI or other assistant tools should:

* Prioritize headless execution, avoid all forms of UI
* Generate automation logic for GUI apps (not backend APIs)
* Focus on GUI scripting, screen scraping, and stealth data handling
* Maintain Windows-specific compatibility, especially with Task Scheduler

## Future Ideas

* Detect and filter duplicate entries
* OCR pre-processing (contrast, grayscale)
* Configuration GUI for admin use (separate from main bot)
* Full logging and heartbeat/status pings to monitor uptime
