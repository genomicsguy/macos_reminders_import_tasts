import subprocess
import sys
import tkinter as tk
from tkinter import scrolledtext, messagebox

# --- Constants ---
DEFAULT_REMINDER_LIST = "Reminders"
CATEGORY_PREFIX = "CATEGORY:" # Lines starting with this will define a new reminder list

def run_applescript(applescript_command):
    """Helper function to run AppleScript commands and handle errors."""
    try:
        # We don't want the output of successful applescript commands printed to console
        process = subprocess.run(["osascript", "-e", applescript_command],
                                 check=True,
                                 capture_output=True,
                                 text=True)
        return process.stdout.strip()
    except subprocess.CalledProcessError as e:
        # Capture stderr for error messages
        raise RuntimeError(f"AppleScript command failed: {e.stderr.strip()}")

def ensure_reminder_list_exists(list_name):
    """
    Checks if a reminder list exists. If not, attempts to create it.
    Returns True if the list exists or was created, False otherwise.
    Provides user feedback via messagebox if running in GUI mode.
    """
    if not list_name:
        return False # Cannot ensure an empty list name

    # AppleScript to check if list exists and create if not
    applescript_check_and_create = f'''
    tell application "Reminders"
        if not (exists list "{list_name}") then
            try
                make new list with properties {{name:"{list_name}"}}
                return "created"
            on error errMsg
                return "error:" & errMsg
            end try
        else
            return "exists"
        end if
    end tell
    '''
    try:
        result = run_applescript(applescript_check_and_create)
        if result == "exists" or result == "created":
            return True
        elif result.startswith("error:"):
            # This path is for when AppleScript explicitly returns an error string
            if 'root' in globals() and root.winfo_exists(): # Check if Tkinter GUI is active
                messagebox.showwarning("List Creation Warning",
                                       f"Couldn't create list '{list_name}':\n{result.split(':', 1)[1]}\n"
                                       f"Tasks for this category will be added to '{DEFAULT_REMINDER_LIST}'.")
            else: # Running via Shortcut
                print(f"Warning: Couldn't create list '{list_name}': {result.split(':', 1)[1]}. Tasks will go to '{DEFAULT_REMINDER_LIST}'.")
            return False
    except RuntimeError as e:
        # This path is for errors caught by subprocess.run (e.g., AppleScript syntax error, Reminders app not running)
        if 'root' in globals() and root.winfo_exists(): # Check if Tkinter GUI is active
            messagebox.showwarning("List Creation Warning",
                                   f"Error checking/creating list '{list_name}':\n{e}\n"
                                   f"Tasks for this category will be added to '{DEFAULT_REMINDER_LIST}'.")
        else: # Running via Shortcut
            print(f"Warning: Error checking/creating list '{list_name}': {e}. Tasks will go to '{DEFAULT_REMINDER_LIST}'.")
        return False
    return False # Fallback

def add_reminder(task_name, reminder_list=DEFAULT_REMINDER_LIST):
    """
    Adds a single reminder to the specified Reminders list using AppleScript.
    """
    applescript_command = f'''
    tell application "Reminders"
        set theList to list "{reminder_list}"
        make new reminder at end of theList with properties {{name:"{task_name}"}}
    end tell
    '''
    run_applescript(applescript_command) # Use the helper function, it will raise RuntimeError on failure

class TaskInputApp:
    def __init__(self, master):
        self.master = master
        master.title("Add Reminders from List")

        # Make the window modal and set a reasonable initial size
        master.transient(master)
        master.grab_set()
        # Set geometry for initial size (widthxheight+x+y)
        # 600 width, 400 height is good for 10-15 lines
        master.geometry("600x400") # You can adjust this size

        self.label = tk.Label(master,
                              text=f"Paste your tasks below, one per line.\n\n"
                                   f"To organize reminders into categories/lists, start a line with:\n"
                                   f"  **{CATEGORY_PREFIX} Your Category Name**\n\n"
                                   f"Tasks not under a category will go into the '{DEFAULT_REMINDER_LIST}' list.",
                              justify=tk.LEFT)
        self.label.pack(pady=10, padx=10, anchor=tk.W)

        # ScrolledText provides built-in scrollbars
        self.text_area = scrolledtext.ScrolledText(master, wrap=tk.WORD, width=70, height=15)
        self.text_area.pack(padx=10, pady=5, fill=tk.BOTH, expand=True) # Fill and expand to use available space

        self.add_button = tk.Button(master, text="Add Reminders", command=self.add_tasks)
        self.add_button.pack(pady=10)

        self.master.protocol("WM_DELETE_WINDOW", self.on_closing) # Handle window close

    def add_tasks(self):
        task_list_string = self.text_area.get("1.0", tk.END).strip()
        if not task_list_string:
            messagebox.showinfo("No Input", "Please enter some tasks.")
            return

        lines = [line.strip() for line in task_list_string.split('\n')]

        current_reminder_list = DEFAULT_REMINDER_LIST
        successful_tasks = []
        failed_tasks = []
        
        # Attempt to ensure the default list exists at the start
        # If it fails, we set a flag so we know not to fall back to it later.
        default_list_creation_successful = ensure_reminder_list_exists(DEFAULT_REMINDER_LIST)
        if not default_list_creation_successful:
            current_reminder_list = None # No reliable default list
            messagebox.showwarning("Default List Issue",
                                   f"Couldn't ensure the default list '{DEFAULT_REMINDER_LIST}' exists. "
                                   "Tasks might not be added correctly without a valid list.")

        for line_num, line in enumerate(lines, 1):
            if not line:
                continue # Skip empty lines

            if line.upper().startswith(CATEGORY_PREFIX.upper()):
                category_name_raw = line[len(CATEGORY_PREFIX):].strip()
                if category_name_raw:
                    if ensure_reminder_list_exists(category_name_raw):
                        current_reminder_list = category_name_raw
                    else:
                        # If category creation fails, revert to default if it's reliable
                        current_reminder_list = DEFAULT_REMINDER_LIST if default_list_creation_successful else None
                        messagebox.showwarning("Category Issue",
                                               f"Line {line_num}: Couldn't use category '{category_name_raw}'. "
                                               f"Falling back to '{current_reminder_list or 'no list'}' for subsequent tasks.")
                else:
                    # CATEGORY: provided but no name after it
                    current_reminder_list = DEFAULT_REMINDER_LIST if default_list_creation_successful else None
                    messagebox.showwarning("Invalid Category",
                                           f"Line {line_num}: Empty category name provided. "
                                           f"Tasks will be added to '{current_reminder_list or 'no list'}' until a new category is defined.")
            else:
                # It's a task line
                task = line
                if current_reminder_list:
                    try:
                        add_reminder(task, current_reminder_list)
                        successful_tasks.append(f"'{task}' in '{current_reminder_list}'")
                    except RuntimeError as e:
                        failed_tasks.append(f"'{task}' to '{current_reminder_list}' (Error: {e})")
                else:
                    failed_tasks.append(f"'{task}' (No valid reminder list available for this task)")


        summary_message = f"Successfully added {len(successful_tasks)} reminders.\n"
        if successful_tasks:
            summary_message += "\nExamples:\n" + "\n".join(successful_tasks[:5]) # Show first 5 successful tasks
            if len(successful_tasks) > 5:
                summary_message += "\n..."

        if failed_tasks:
            summary_message += f"\n\nFailed to add {len(failed_tasks)} reminders:\n"
            summary_message += "\n".join(failed_tasks)
            messagebox.showerror("Reminders Added (with Errors)", summary_message)
        else:
            messagebox.showinfo("Reminders Added", summary_message)
        
        self.master.destroy()

    def on_closing(self):
        self.master.destroy() # Close the window

# --- Main execution logic for Apple Shortcuts ---
def process_tasks_from_string(task_list_string):
    """
    Processes a multi-line string of tasks and adds them to Reminders.
    Used when called from Apple Shortcuts (stdin). Prints output to console.
    """
    if not task_list_string:
        print("No tasks entered.")
        return

    lines = [line.strip() for line in task_list_string.split('\n')]

    current_reminder_list = DEFAULT_REMINDER_LIST
    
    default_list_creation_successful = ensure_reminder_list_exists(DEFAULT_REMINDER_LIST)
    if not default_list_creation_successful:
        current_reminder_list = None 
        print(f"Warning: Couldn't ensure the default list '{DEFAULT_REMINDER_LIST}' exists. Tasks might not be added.")

    for line in lines:
        if not line:
            continue

        if line.upper().startswith(CATEGORY_PREFIX.upper()):
            category_name_raw = line[len(CATEGORY_PREFIX):].strip()
            if category_name_raw:
                if ensure_reminder_list_exists(category_name_raw):
                    current_reminder_list = category_name_raw
                else:
                    current_reminder_list = DEFAULT_REMINDER_LIST if default_list_creation_successful else None
                    print(f"Warning: Couldn't use category '{category_name_raw}'. Falling back to default list.")
            else:
                current_reminder_list = DEFAULT_REMINDER_LIST if default_list_creation_successful else None
                print("Warning: Empty category name provided. Tasks will go to default list.")
        else:
            task = line
            if current_reminder_list:
                try:
                    add_reminder(task, current_reminder_list)
                    print(f"Added: '{task}' to '{current_reminder_list}'")
                except RuntimeError as e:
                    print(f"Failed to add '{task}' to '{current_reminder_list}': {e}")
            else:
                print(f"Skipping task '{task}': No valid reminder list available.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--from-shortcut":
        # When called by Apple Shortcuts, it passes input via stdin
        task_list_string = sys.stdin.read()
        process_tasks_from_string(task_list_string)
    else:
        # When run directly, open the GUI modal
        root = tk.Tk()
        app = TaskInputApp(root)
        root.mainloop()
