# Apple Reminders List Importer

This script and accompanying Apple Shortcut provide a convenient way to import a multi-line list of tasks into your Apple Reminders app, with support for organizing tasks into specific reminder lists (categories).

## Features

  * **Batch Import:** Add multiple tasks to Reminders from a plain text list.
  * **Categorization:** Organize tasks into existing or new Reminder lists using special "CATEGORY:" headings.
  * **Default List Fallback:** Tasks not under a specific category automatically go into your main "Reminders" list.
  * **User-Friendly Input:** Utilizes an Apple Shortcut to provide a native input modal, or a Tkinter GUI for direct script execution.
  * **Error Handling:** Provides feedback on successful and failed task additions, and warnings for issues like uncreatable reminder lists.

## How It Works

The system consists of two main parts:

1.  **Python Script (`import_reminders.py`):** This script contains the core logic. It parses your input list, identifies categories, and uses AppleScript commands (executed via `osascript`) to interact with the macOS Reminders application to create lists and add tasks.
2.  **Apple Shortcut:** This acts as the user interface. It prompts you for your list of tasks and then passes that text to the Python script for processing.

## Setup Instructions

### Step 1: Save the Python Script

1.  **Download the script:** Copy the entire Python code from the last response into a new file.

2.  **Save the file:** Name it `import_reminders.py`.

3.  **Choose a stable location:** A good practice is to create a dedicated folder for your scripts that won't accidentally be moved or deleted. A recommended location is:

      * `~/Scripts/` (i.e., `/Users/YOUR_USERNAME/Scripts/`)
      * Or, if you prefer, `~/Documents/Scripts/`

    For example, save it as: `/Users/YOUR_USERNAME/Scripts/import_reminders.py`

### Step 2: Make the Script Executable (Optional but Recommended)

This step ensures that your operating system has the correct permissions to run the script.

1.  Open **Terminal.app**.
2.  Run the following command, replacing `/path/to/your/script/` with the actual path where you saved `import_reminders.py`:
    ```bash
    chmod +x /Users/YOUR_USERNAME/Scripts/import_reminders.py
    ```
    (Replace `YOUR_USERNAME` with your actual macOS username).

### Step 3: Create the Apple Shortcut

1.  **Open the Shortcuts app** on your Mac.

2.  Click the **`+` icon** to create a new Shortcut.

3.  **Add "Ask for Input" Action:**

      * Search for "Ask for Input" and drag it into your shortcut.
      * **Prompt:** `Paste your to-do list, one item per line:`
      * **Input Type:** `Text`

4.  **Add "Run Shell Script" Action:**

      * Search for "Run Shell Script" and drag it below the "Ask for Input" action.
      * **Crucial Settings:**
          * **Shell:** Set this to your Python 3 interpreter. If you installed Python via Homebrew, this is typically `/opt/homebrew/bin/python3`. If you're unsure, open Terminal and type `which python3` to find its path.

          * **Input:** Ensure this is set to the magic variable that represents the output of your "Ask for Input" action. It should automatically show `Ask for Input`.

          * **Pass Input:** **Select `to stdin`**. This is vital for the script to receive your pasted text.

          * **Script:** Enter the full, **quoted** path to your `import_reminders.py` script, followed by the `--from-shortcut` argument.

            **Example Script Content:**

            ```bash
            /opt/homebrew/bin/python3 "/Users/YOUR_USERNAME/Scripts/import_reminders.py" --from-shortcut
            ```

            *(Remember to replace `YOUR_USERNAME` with your actual macOS username and `/opt/homebrew/bin/python3` with your correct Python 3 path if different).*

    Here's what your "Run Shell Script" action should look like in the Shortcuts app:

### Step 4: Run Your Shortcut

1.  **Execute the Shortcut:**

      * Run it directly from the Shortcuts app.
      * For quick access, you can right-click the Shortcut in the app and select "Shortcut Details" -\> "Pin to Menu Bar" or "Add to Dock".
      * You can also assign a keyboard shortcut to it.

2.  **Provide Input:** A modal window will appear. Paste or type your list of tasks.

#### Input Format

  * **Simple List:** Just paste your tasks, one per line. They will all go to your default "Reminders" list.

    ```
    Task 1
    Task 2
    Another item
    ```

  * **Categorized List:** To organize tasks into different Reminder lists, use the `CATEGORY:` prefix followed by the desired list name.

    ```
    Task for main Reminders list

    CATEGORY: Groceries
    Milk
    Eggs
    Bread

    CATEGORY: Work Projects
    Finish Q2 Report
    Schedule team sync
    Email client X

    Task for main Reminders list again
    ```

      * If a list specified by `CATEGORY:` doesn't exist, the script will attempt to create it.
      * Tasks under a `CATEGORY:` heading will be added to that specific Reminders list until a new `CATEGORY:` is encountered or the list ends.
      * Tasks not explicitly under a `CATEGORY:` heading will be added to your default "Reminders" list.
