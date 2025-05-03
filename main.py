# IGNORE_WHEN_COPYING_START
# content_copy
# download
# Use code with caution.
# IGNORE_WHEN_COPYING_END
import os
import platform
import shutil
import json
import inspect
import subprocess  # For running external commands
import requests  # For downloading files
from urllib.parse import urlparse  # For extracting filename from URL
import time
import random
import traceback # For printing full errors in main loop
import shlex # For better command splitting
import re # Needed for calculating clean text width (optional but good)

# ANSI escape codes for colors
RED = '\033[91m'
ORANGE = '\033[38;5;208m'  # A good orange color
YELLOW = '\033[93m'
GREEN = '\033[92m'
BLUE = '\033[94m'
PURPLE = '\033[95m'
RESET = '\033[0m'

# --- Constants ---
ROOT_DIR_NAME = "root"  # Customize this if you want a different root name
ROOT_PATH = os.path.abspath("./")  # Define the root path globally
USER_CONFIG_FILE = os.path.join(ROOT_PATH, "user.json")
APPLICATIONS_DIR = os.path.join(ROOT_PATH, "applications")  # Directory for applications
REPO_FILE = os.path.join(ROOT_PATH, "repo.txt") # Repository file
DEFAULT_REPO_URL = "https://raw.githubusercontent.com/AxoIsAxo/null.os/refs/heads/main/repo.txt" # Default repo URL
try:
    MAIN_SCRIPT = os.path.basename(__file__) # Name of current script
except NameError:
    MAIN_SCRIPT = "mypythonos_script.py" # Fallback name if __file__ is not defined (e.g. interactive)


# --- Global State ---
INSTALLED_APPS = {}  # Dictionary to store installed applications info {command: {info}}
APP_REPOSITORY = {} # Dictionary to store name: url mappings from repo.txt {name: url}
username = "user"   # Default username, loaded/created later
hostname = "mypythos" # Default hostname, loaded/created later

# --- Configuration and Loading ---

def load_user_config():
    """Loads user configuration from user.json."""
    if os.path.exists(USER_CONFIG_FILE):
        try:
            with open(USER_CONFIG_FILE, "r") as f:
                config = json.load(f)
            return config.get("username", "user"), config.get("hostname", "hostname")
        except json.JSONDecodeError:
            print(f"{YELLOW}Warning: Could not decode user.json. Using defaults.{RESET}")
            return "user", "hostname"
    else:
        return None, None

def create_user_config():
    """Creates user configuration file and prompts for username and hostname."""
    _username = input("Enter username: ").strip()
    if not _username: _username = "user" # Default if empty
    _hostname = input("Enter hostname: ").strip()
    if not _hostname: _hostname = "mypythos" # Default if empty

    config = {"username": _username, "hostname": _hostname}

    try:
        with open(USER_CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
        print(f"{GREEN}User configuration saved to user.json{RESET}")
        return _username, _hostname
    except OSError as e:
        print(f"{RED}Error: Could not create user.json: {e}{RESET}")
        return "user", "mypythos"  # Provide defaults in case of error


def load_repository():
    """Loads application repository information from repo.txt."""
    global APP_REPOSITORY
    APP_REPOSITORY.clear() # Clear previous entries before loading

    if not os.path.exists(REPO_FILE):
        # Don't print warning if it's the first run and file doesn't exist yet
        # The main setup handles the initial download attempt.
        # print(f"{YELLOW}Repository file '{os.path.basename(REPO_FILE)}' not found or is empty.{RESET}")
        return

    try:
        with open(REPO_FILE, "r") as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith('#')] # Read non-empty, non-comment lines

        if not lines:
             # print(f"{YELLOW}Repository file '{os.path.basename(REPO_FILE)}' is empty or contains only comments.{RESET}")
             return

        if len(lines) % 2 != 0:
            print(f"{YELLOW}Warning: Malformed repository file '{os.path.basename(REPO_FILE)}'. Odd number of lines after comments. Ignoring last line.{RESET}")
            lines = lines[:-1] # Ignore the last line

        entries_loaded = 0
        for i in range(0, len(lines), 2):
            name = lines[i]
            url = lines[i+1]
            if name and url: # Ensure neither is empty
                if name in APP_REPOSITORY:
                     print(f"{YELLOW}Warning: Duplicate repository entry '{name}'. Using last definition.{RESET}")
                APP_REPOSITORY[name] = url
                entries_loaded += 1
            else:
                print(f"{YELLOW}Warning: Invalid entry skipped in '{os.path.basename(REPO_FILE)}' near line {i+1} (original file line number may differ).{RESET}")

        if entries_loaded > 0:
            print(f"{GREEN}Loaded {entries_loaded} entries from repository.{RESET}")

    except OSError as e:
        print(f"{RED}Error reading repository file '{os.path.basename(REPO_FILE)}': {e}{RESET}")
    except Exception as e:
        print(f"{RED}An unexpected error occurred while loading repository: {e}{RESET}")


# --- ASCII Art & Neofetch ---

NEOFETCH_ART = f"""
{RED}             ####              #        ###     ###                                                         ##
      ########         #####  #########        ########  ######  #######                           #############          ##############{ORANGE}
          #########       ######  #########        ########  ######   ######                         #################       #################
 ##########      #  ###  #########        #### ###  ######  #######                        #########  # ######    # #####     #######{YELLOW}
           ##########     #######  #  #####        ##### ##  ######  ######                         #######     ########   #####         ##
 #### #######    #######     #####        ########  ######  ######                         #######       ## ###   #######{GREEN}
          ###### ######    ######  ## #####        ########  ######  ######                      #  #######       ######   ######### ##
 ######  ####### #######  ########        ########  ## ###   # ####     ###########  ####  #######      #######     ##############{BLUE}
          ######   ####### ######  ######          ##### ##  ######  ######     ###     ########    #######       #######       #############
 ######    ############  ########        ########  ######  ######                         #######      ### ####            ##########{PURPLE}
           ######     ###########  ########        ########  # ####  ## ###                         #######      ### ###                #######
 ######      ##########  #########     ##########  ######  #######                        #######      #######    ####        ####  #{RED}
           ######       #########  ########################  ######  #######                        #########  ########   ##########   #######
 ######        ########   #####  ####  # ########  ######  #######                         ##################     ##################{ORANGE}
           ######         #######    ###########   ########  #######  ######                           ##############         ##############
                                      ###                                                                   ##                     ##

{RESET}""" # Add the reset AFTER the art

# Helper to remove ANSI codes for width calculation
ANSI_ESCAPE_RE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def calculate_visual_width(text):
    """Calculates the visual width of a string by removing ANSI escape codes."""
    return len(ANSI_ESCAPE_RE.sub('', text))

# Calculate the required width for the art (do this once)
NEOFETCH_ART_LINES = NEOFETCH_ART.strip('\n').split('\n')
NEOFETCH_ART_MIN_WIDTH = 0
for line in NEOFETCH_ART_LINES:
    NEOFETCH_ART_MIN_WIDTH = max(NEOFETCH_ART_MIN_WIDTH, calculate_visual_width(line))
NEOFETCH_ART_MIN_WIDTH += 2 # Add a little padding

def neofetch():
    """Displays system information, adapting to terminal width.
    Usage: neofetch"""
    DEFAULT_WIDTH = 80 # Default if size cannot be determined

    try:
        terminal_width = os.get_terminal_size().columns
    except OSError:
        print(f"{YELLOW}Warning: Could not determine terminal size. Assuming width {DEFAULT_WIDTH}.{RESET}")
        terminal_width = DEFAULT_WIDTH

    # --- Display Art or Title ---
    if terminal_width >= NEOFETCH_ART_MIN_WIDTH:
        print(NEOFETCH_ART)
    else:
        # Print a simple centered title if art doesn't fit
        title = "--- MyPythonOS Info ---"
        clean_title_len = calculate_visual_width(title) # Should be same as len() here
        if terminal_width >= clean_title_len:
            padding = (terminal_width - clean_title_len) // 2
            print(" " * padding + title)
        else:
            print(title) # Print even if it wraps
        print("-" * terminal_width) # Separator line matching terminal width

    # --- Gather System Info ---
    os_name = "MyPythonOS"
    kernel = platform.system()
    architecture = platform.machine()
    python_version = platform.python_version()
    cwd = os.getcwd()
    try:
        num_files = len([f for f in os.listdir(cwd) if os.path.isfile(os.path.join(cwd, f))])
        num_dirs = len([d for d in os.listdir(cwd) if os.path.isdir(os.path.join(cwd, d))])
    except OSError as e:
        print(f"{YELLOW}Warning: Could not count files/dirs in CWD: {e}{RESET}")
        num_files = "N/A"
        num_dirs = "N/A"

    # Use the relative path logic for CWD display (like in get_prompt)
    display_path = ""
    root_path_abs = os.path.abspath(ROOT_PATH)
    cwd_abs = os.path.abspath(cwd)
    if cwd_abs == root_path_abs: display_path = "~"
    elif cwd_abs.startswith(root_path_abs + os.sep): # Check if it starts with root + separator
         relative_path = os.path.relpath(cwd_abs, root_path_abs)
         display_path = f"~/{relative_path.replace(os.sep, '/')}"
    else: display_path = cwd_abs # Show full path if outside root

    # --- Display System Info ---
    # Simple key-value print, relying on terminal wrapping
    print(f"""
OS: {os_name}
Kernel: {kernel}
Architecture: {architecture}
Python: {python_version}
Files in CWD: {num_files}
Dirs in CWD: {num_dirs}
CWD: {display_path}
""")
    # Optional: Add a bottom separator matching terminal width
    # print("-" * terminal_width)


# --- Core File System Commands ---

def ls(args=None):
    """Lists files and directories in the current directory.
    Usage: ls [-l]"""
    if args is None: args = [] # Ensure args is a list
    try:
        detailed = False
        if args and args[0] == "-l":
            detailed = True
            # Remove '-l' from args if other args might be added later
            args = args[1:]

        # Could add support for listing specific directory later:
        # target_dir = args[0] if args else os.getcwd()
        target_dir = os.getcwd()

        items = sorted(os.listdir(target_dir)) # Sort alphabetically

        for item in items:
            try:
                 item_path = os.path.join(target_dir, item) # Use target_dir
                 if detailed:
                     # Basic detailed view
                     stat_info = os.stat(item_path)
                     size = stat_info.st_size
                     # Add more details like permissions, date later if needed
                     if os.path.isdir(item_path):
                         print(f"{BLUE}d {size:>10} {item}/{RESET}")
                     elif os.path.isfile(item_path):
                         print(f"- {size:>10} {item}{RESET}")
                     else:
                         print(f"? {size:>10} {item}{RESET}") # Other type
                 else:
                     # Colorized output
                     if os.path.isdir(item_path):
                         print(f"{BLUE}{item}{RESET}/")
                     elif os.path.isfile(item_path) and os.access(item_path, os.X_OK) and os.name != 'nt':
                          print(f"{GREEN}{item}{RESET}*")
                     elif os.path.isfile(item_path) and item.split('.')[-1].lower() in ['exe', 'bat', 'com', 'cmd'] and os.name == 'nt':
                          print(f"{GREEN}{item}{RESET}*")
                     elif os.path.isfile(item_path):
                          print(item)
                     else:
                          print(f"{ORANGE}{item}{RESET}")
            except OSError:
                 print(f"{RED}Error reading: {item}{RESET}")

    except FileNotFoundError:
        print(f"{RED}Error: Directory not found: {target_dir}{RESET}")
    except OSError as e:
        print(f"{RED}Error listing directory: {e}{RESET}")


def delf(args):
    """Deletes a file.
    Usage: delf <filename>"""
    if not args:
        print("Usage: delf <filename>")
        return
    filename = args[0] # Expecting only one argument
    try:
        target_path_abs = os.path.abspath(filename)
        critical_files_abs = [os.path.abspath(p) for p in [USER_CONFIG_FILE, REPO_FILE, MAIN_SCRIPT]]
        if target_path_abs in critical_files_abs:
            print(f"{RED}Error: Cannot delete critical system file '{os.path.basename(filename)}' using delf.{RESET}")
            return
        os.remove(filename)
        print(f"Deleted file: {filename}")
    except FileNotFoundError:
        print(f"{RED}Error: File not found: {filename}{RESET}")
    except IsADirectoryError:
        print(f"{RED}Error: '{filename}' is a directory. Use 'deld' to delete directories.{RESET}")
    except PermissionError:
        print(f"{RED}Error: Permission denied to delete '{filename}'.{RESET}")
    except OSError as e:
        print(f"{RED}Error deleting file '{filename}': {e}{RESET}")


def deld(args):
    """Deletes a directory (recursively).
    Usage: deld <directory>"""
    if not args:
        print("Usage: deld <directory>")
        return
    dirname = args[0] # Expecting only one argument

    try:
        target_path = os.path.abspath(dirname)
        root_path_abs = os.path.abspath(ROOT_PATH)
        current_path_abs = os.path.abspath(os.getcwd())
        apps_dir_abs = os.path.abspath(APPLICATIONS_DIR)

        # Safety checks
        if target_path == root_path_abs:
             print(f"{RED}Error: Cannot delete the root directory ('{ROOT_DIR_NAME}').{RESET}")
             return
        if target_path == current_path_abs:
             print(f"{RED}Error: Cannot delete the current working directory. 'cd' out first.{RESET}")
             return
        if target_path == apps_dir_abs:
             print(f"{RED}Error: Cannot delete the main applications directory ('{os.path.basename(APPLICATIONS_DIR)}') using deld.{RESET}")
             print(f"{YELLOW}Delete individual app directories inside it if needed.{RESET}")
             return
        # Prevent deleting parent of root (more robust check)
        # This check might be too strict if ROOT_PATH is '.'
        # if os.path.commonpath([root_path_abs, target_path]) != root_path_abs and target_path == os.path.dirname(root_path_abs):
        #      print(f"{RED}Error: Cannot delete the parent directory of the OS root.{RESET}")
        #      return

        shutil.rmtree(target_path)
        print(f"Deleted directory: {dirname}")
    except FileNotFoundError:
        print(f"{RED}Error: Directory not found: {dirname}{RESET}")
    except NotADirectoryError:
         print(f"{RED}Error: '{dirname}' is not a directory.{RESET}")
    except PermissionError:
         print(f"{RED}Error: Permission denied to delete directory '{dirname}'.{RESET}")
    except OSError as e: # Catches 'Directory not empty' on some OS if it's not rmtree-able?
        print(f"{RED}Error deleting directory '{dirname}': {e}{RESET}")


def cd(args):
    """Changes the current directory. 'cd ~' or 'cd' goes to root.
    Usage: cd [<directory> | ~]"""
    target_dir = ROOT_PATH # Default target is root
    directory = args[0] if args else None

    if directory and directory != "~":
        target_dir = directory

    try:
        # Add stricter path checking if needed to prevent escaping ROOT_PATH
        # tentative_path = os.path.abspath(os.path.join(os.getcwd(), target_dir))
        # root_abs = os.path.abspath(ROOT_PATH)
        # if not tentative_path.startswith(root_abs): # Basic check
        #    print(f"{RED}Error: Cannot 'cd' outside the root directory '{ROOT_PATH}'.{RESET}")
        #    return

        os.chdir(target_dir)
    except FileNotFoundError:
        print(f"{RED}Error: Directory not found: {target_dir}{RESET}")
    except NotADirectoryError:
        print(f"{RED}Error: Not a directory: {target_dir}{RESET}")
    except PermissionError:
         print(f"{RED}Error: Permission denied to change directory to '{target_dir}'.{RESET}")
    except OSError as e:
        print(f"{RED}Error changing directory: {e}{RESET}")


def pwd():
    """Prints the current working directory path relative to root (~).
    Usage: pwd"""
    try:
        # Use the same relative path logic as prompt/neofetch
        cwd = os.getcwd()
        display_path = ""
        root_path_abs = os.path.abspath(ROOT_PATH)
        cwd_abs = os.path.abspath(cwd)
        if cwd_abs == root_path_abs:
            display_path = "~"
        elif cwd_abs.startswith(root_path_abs + os.sep): # Check if it starts with root + separator
            relative_path = os.path.relpath(cwd_abs, root_path_abs)
            display_path = f"~/{relative_path.replace(os.sep, '/')}"
        else:
            display_path = cwd_abs # Show full path if outside root
        print(display_path)
    except OSError as e:
        print(f"{RED}Error getting current directory: {e}{RESET}")


def mkdir(args):
    """Creates a new directory. Creates parent directories as needed.
    Usage: mkdir <directory>"""
    if not args:
        print("Usage: mkdir <directory>")
        return
    dirname = args[0]
    try:
        os.makedirs(dirname, exist_ok=True)
        print(f"Created directory: {dirname}")
    except PermissionError:
        print(f"{RED}Error: Permission denied to create directory '{dirname}'.{RESET}")
    except OSError as e:
        print(f"{RED}Error: Could not create directory '{dirname}': {e}{RESET}")


def touch(args):
    """Creates a new empty file or updates its timestamp.
    Usage: touch <filename>"""
    if not args:
        print("Usage: touch <filename>")
        return
    filename = args[0]
    try:
        if os.path.isdir(filename):
            print(f"{RED}Error: '{filename}' is a directory.{RESET}")
            return

        parent_dir = os.path.dirname(filename)
        if parent_dir and not os.path.exists(parent_dir):
             os.makedirs(parent_dir, exist_ok=True) # Ensure parent exists

        if os.path.exists(filename):
            os.utime(filename, None) # Update timestamp
        else:
            with open(filename, 'a'): pass # Create empty file
        # No output on success for typical 'touch' behavior
    except PermissionError:
        print(f"{RED}Error: Permission denied for file operation on '{filename}'.{RESET}")
    except OSError as e:
        print(f"{RED}Error creating/updating file '{filename}': {e}{RESET}")


def move(args):
    """Moves or renames a file or directory.
    Usage: move <source> <destination>"""
    if len(args) != 2:
        print("Usage: move <source> <destination>")
        return
    source, destination = args[0], args[1]
    try:
        src_abs = os.path.abspath(source)
        critical_abs = [os.path.abspath(p) for p in [USER_CONFIG_FILE, REPO_FILE, MAIN_SCRIPT, APPLICATIONS_DIR]]
        if src_abs in critical_abs:
            print(f"{RED}Error: Cannot move critical system item '{source}' using move.{RESET}")
            return

        # Ensure destination directory exists if moving into a directory
        if os.path.exists(destination) and os.path.isdir(destination) and not os.path.exists(source):
            print(f"{RED}Error: Source '{source}' not found.{RESET}")
            return
        if os.path.exists(destination) and os.path.isdir(destination):
             # shutil.move handles moving *into* a directory automatically
             pass
        elif not os.path.exists(os.path.dirname(destination)) and os.path.dirname(destination):
             # Create parent directory for destination if renaming/moving to a new path
             try:
                 os.makedirs(os.path.dirname(destination))
             except OSError as e:
                 print(f"{RED}Error creating destination directory '{os.path.dirname(destination)}': {e}{RESET}")
                 return

        shutil.move(source, destination)
        print(f"Moved: {source} to {destination}")
    except FileNotFoundError:
        print(f"{RED}Error: Source '{source}' not found.{RESET}")
    except shutil.Error as e: # Handles dest exists, etc.
        print(f"{RED}Error moving '{source}' to '{destination}': {e}{RESET}")
    except PermissionError:
         print(f"{RED}Error: Permission denied during move operation.{RESET}")
    except OSError as e:
        print(f"{RED}Error: Could not move '{source}' to '{destination}': {e}{RESET}")


# --- Utility and External Commands ---

def help():
    """Displays available commands and their usage."""
    print("Available commands:")
    commands = {}
    # Built-in commands defined in this script
    built_in_funcs = [
        ls, delf, deld, cd, pwd, mkdir, touch, move, help, clear, edit, javac,
        run, download, install, repo, cowsay, delpanic, neofetch
    ]
    for func in built_in_funcs:
        commands[func.__name__] = func

    # Installed apps
    for name, info in INSTALLED_APPS.items():
        if name not in commands:
            commands[name] = f"Runs the '{info['name']}' application (v{info['version']})"

    if not commands:
        print("  (No commands available)")
        return

    max_len = max(len(name) for name in commands.keys())

    for name in sorted(commands.keys()):
        obj = commands[name]
        color = GREEN if callable(obj) else BLUE # Green for built-in, Blue for apps
        print(f"  {color}{name:<{max_len}}{RESET} : ", end="")

        if callable(obj):
            docstring = inspect.getdoc(obj)
            if docstring:
                lines = docstring.splitlines()
                print(lines[0]) # Print short description
                # Indent and print usage/details
                for line in lines[1:]: print(f"    {line.strip()}")
            else: print("(No help available)")
        elif isinstance(obj, str):
             print(f"{PURPLE}{obj}{RESET}") # Print app description in purple

    print("\nCommands can be chained with '|' (e.g., cmd1 | cmd2)")


def clear():
    """Clears the terminal screen.
    Usage: clear"""
    os.system('cls' if os.name == 'nt' else 'clear')


def edit(args):
    """Edits a file using nano (or notepad), creates if non-existent.
    Usage: edit <filename>"""
    if not args:
        print("Usage: edit <filename>")
        return
    filename = args[0]

    editor = None
    if shutil.which("nano"):
        editor = "nano"
    elif os.name == 'nt' and shutil.which("notepad"):
        editor = "notepad"
    else:
        print(f"{RED}Error: Text editor ('nano' or 'notepad') not found in PATH.{RESET}")
        return

    try:
        abs_filename = os.path.abspath(filename)

        # Prevent editing really critical files? Maybe just warn.
        critical_files_abs = [os.path.abspath(p) for p in [MAIN_SCRIPT]] # User/repo editing is handled
        if abs_filename in critical_files_abs:
            print(f"{YELLOW}Warning: Editing core OS script '{os.path.basename(filename)}'. Be careful!{RESET}")


        if not os.path.exists(abs_filename):
             parent_dir = os.path.dirname(abs_filename)
             if parent_dir and not os.path.exists(parent_dir):
                 os.makedirs(parent_dir, exist_ok=True)
             touch([filename]) # Create empty file if it doesn't exist

        # Use check=False for notepad as it often detaches
        use_check = editor == "nano"
        subprocess.run([editor, abs_filename], check=use_check)

        # Post-Edit Actions - Reload relevant configs
        if abs_filename == os.path.abspath(REPO_FILE):
            print(f"{YELLOW}Repository file edited. Reloading repository...{RESET}")
            load_repository()
        elif abs_filename == os.path.abspath(USER_CONFIG_FILE):
             print(f"{YELLOW}User config edited. Changes may apply on next restart.{RESET}")
             # Could reload username/hostname here if desired
             global username, hostname
             _uname, _hname = load_user_config()
             if _uname and _hname:
                 username = _uname
                 hostname = _hname
                 print(f"{GREEN}Username/Hostname reloaded for current session.{RESET}")
        elif abs_filename.endswith("app.conf") and abs_filename.startswith(os.path.abspath(APPLICATIONS_DIR)):
             print(f"{YELLOW}Application configuration edited. Reloading applications...{RESET}")
             load_applications()

    except FileNotFoundError:
        print(f"{RED}Error: Editor '{editor}' failed to run.{RESET}")
    except subprocess.CalledProcessError as e:
        # Only show error for nano where check=True
        print(f"{YELLOW}Editor '{editor}' closed (exit code {e.returncode}).{RESET}")
    except PermissionError:
        print(f"{RED}Error: Permission denied to access or modify '{filename}'.{RESET}")
    except OSError as e:
        print(f"{RED}Error preparing file for editing: {e}{RESET}")
    except Exception as e:
        print(f"{RED}An unexpected error occurred during editing: {e}{RESET}")


def download_file(url, filepath):
    """Helper function to download a file from a URL to a specific path."""
    print(f"Downloading {os.path.basename(url)} -> {os.path.basename(filepath)} ... ", end="", flush=True)
    try:
        parent_dir = os.path.dirname(filepath)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)

        # Add a User-Agent
        headers = {'User-Agent': f'MyPythonOS Downloader/1.4 ({platform.system()}; Python/{platform.python_version()})'}
        response = requests.get(url, stream=True, headers=headers, timeout=30, allow_redirects=True)
        response.raise_for_status() # Check for 4xx/5xx errors

        # Check content type? Could add basic checks here if desired.
        # content_type = response.headers.get('content-type')

        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"{GREEN}Success{RESET}")
        return True

    except requests.exceptions.Timeout:
        print(f"{RED}Failed (Timeout){RESET}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"{RED}Failed ({e}){RESET}")
        # Clean up partially downloaded file
        if os.path.exists(filepath):
             try: os.remove(filepath)
             except OSError: pass
        return False
    except PermissionError:
         print(f"{RED}Failed (Permission Denied writing to '{os.path.relpath(filepath, ROOT_PATH)}'){RESET}")
         return False
    except OSError as e:
        print(f"{RED}Failed (File System Error: {e}){RESET}")
        return False
    except Exception as e:
        print(f"{RED}Failed (Unexpected Error: {e}){RESET}")
        # Clean up partially downloaded file
        if os.path.exists(filepath):
             try: os.remove(filepath)
             except OSError: pass
        return False


def download(args):
    """Downloads a file from a URL. Saves to CWD or specified location.
    Usage: download <url> [directory_or_filename]"""
    if not args:
        print("Usage: download <url> [directory_or_filename]")
        return
    url = args[0]
    destination = args[1] if len(args) > 1 else None

    try:
        parsed_url = urlparse(url)
        if not parsed_url.scheme in ['http', 'https']:
             print(f"{RED}Error: Invalid URL scheme. Use http or https.{RESET}")
             return

        # Try to get a better filename (e.g., from Content-Disposition header) - More advanced
        # For now, stick to URL path basename
        filename = os.path.basename(parsed_url.path) if parsed_url.path else None
        if not filename:
             timestamp = time.strftime("%Y%m%d-%H%M%S")
             filename = f"download_{timestamp}.dat" # Add a default extension
             print(f"{YELLOW}Could not determine filename from URL path. Using default: '{filename}'.{RESET}")

        filepath = ""
        if destination:
            dest_path = os.path.abspath(destination) # Work with absolute paths
            if os.path.isdir(dest_path):
                filepath = os.path.join(dest_path, filename)
            else:
                 # Treat destination as full filename path
                 filepath = dest_path
                 dest_dir = os.path.dirname(filepath)
                 if dest_dir and not os.path.exists(dest_dir):
                     try:
                         print(f"Creating destination directory: {os.path.relpath(dest_dir, ROOT_PATH)}")
                         os.makedirs(dest_dir, exist_ok=True)
                     except OSError as e:
                         print(f"{RED}Error creating destination directory '{os.path.relpath(dest_dir, ROOT_PATH)}': {e}{RESET}")
                         return
        else:
            filepath = os.path.join(os.getcwd(), filename) # Save to CWD

        target_path_abs = os.path.abspath(filepath)
        critical_files_abs = [os.path.abspath(p) for p in [USER_CONFIG_FILE, REPO_FILE, MAIN_SCRIPT]]
        if target_path_abs in critical_files_abs:
            print(f"{RED}Error: Cannot overwrite critical system file '{os.path.basename(filepath)}' using download.{RESET}")
            return

        # Check if file exists before downloading?
        if os.path.exists(filepath):
            overwrite = input(f"{YELLOW}File '{os.path.relpath(filepath, ROOT_PATH)}' already exists. Overwrite? (y/N): {RESET}").lower()
            if overwrite != 'y':
                print("Download cancelled.")
                return

        download_file(url, filepath)

    except Exception as e:
        print(f"{RED}An unexpected error occurred during download setup: {e}{RESET}")


def javac(args):
    """Compiles a Java file using javac.
    Usage: javac <filename.java>"""
    if not args or not args[0].endswith(".java"):
        print("Usage: javac <filename.java>")
        return
    filename = args[0]
    try:
        if not os.path.isfile(filename):
            print(f"{RED}Error: Java source file not found: {filename}{RESET}")
            return

        compiler = "javac"
        if not shutil.which(compiler):
            print(f"{RED}Error: '{compiler}' command not found (JDK required in PATH).{RESET}")
            return

        print(f"Compiling {filename}...")
        # Run in the directory of the source file for relative imports? Or current dir?
        # Let's stick with current dir for now.
        result = subprocess.run([compiler, filename], check=False, capture_output=True, text=True, encoding='utf-8', errors='replace')

        if result.returncode == 0:
            print(f"{GREEN}Successfully compiled: {filename}{RESET}")
            if result.stderr: print(f"{YELLOW}Compiler Warnings:\n{result.stderr.strip()}{RESET}")
            if result.stdout: print(f"{YELLOW}Compiler Output:\n{result.stdout.strip()}{RESET}") # javac often prints nothing on success
        else:
            print(f"{RED}Error: Compilation failed for {filename}.{RESET}")
            # Print both stdout and stderr as errors can appear in either
            if result.stdout: print(f"Stdout:\n{result.stdout.strip()}")
            if result.stderr: print(f"Stderr:\n{result.stderr.strip()}")

    except Exception as e:
        print(f"{RED}An unexpected error occurred during Java compilation: {e}{RESET}")


def run(args):
    """Runs a code file (Python, Java Class, Lua, JS, Shell) or executable.
    Usage: run <filename> [args...]"""
    if not args:
        print("Usage: run <filename> [args...]")
        return

    filename = args[0]
    script_args = args[1:] # Arguments to pass to the script/executable
    interpreter = None
    cmd = []
    file_to_run = filename

    try:
        if not os.path.exists(file_to_run):
             print(f"{RED}Error: File not found: {file_to_run}{RESET}")
             return
        if os.path.isdir(file_to_run):
             print(f"{RED}Error: Cannot run a directory: {file_to_run}{RESET}")
             return

        ext = os.path.splitext(filename)[1].lower()
        abs_file_to_run = os.path.abspath(file_to_run) # Use absolute path for execution context

        supported = True
        if ext == ".py":
            if shutil.which("python3"): interpreter = "python3"
            elif shutil.which("python"): interpreter = "python"
            else: raise FileNotFoundError("No Python interpreter ('python3' or 'python') found")
            cmd = [interpreter, abs_file_to_run] + script_args
        elif ext == ".class":
            if not shutil.which("java"): raise FileNotFoundError("'java' command not found (JRE/JDK needed)")
            class_name = os.path.splitext(os.path.basename(filename))[0]
            class_dir = os.path.dirname(abs_file_to_run) # Directory containing the class file
            cmd = ["java", "-cp", class_dir, class_name] + script_args
            print(f"Attempting to run Java class: {class_name} (classpath={os.path.relpath(class_dir, ROOT_PATH)})")
        elif ext == ".lua":
             if not shutil.which("lua"): raise FileNotFoundError("'lua' command not found")
             cmd = ["lua", abs_file_to_run] + script_args
        elif ext == ".js":
            if not shutil.which("node"): raise FileNotFoundError("'node' command not found (Node.js needed)")
            cmd = ["node", abs_file_to_run] + script_args
        elif ext in [".sh", ".bash"]:
             # Prefer bash if available
             if shutil.which("bash"): interpreter = "bash"
             elif shutil.which("sh"): interpreter = "sh"
             else: raise FileNotFoundError("No Shell interpreter ('bash' or 'sh') found")
             # Check execute permission on non-Windows
             if os.name != 'nt' and not os.access(abs_file_to_run, os.X_OK):
                 print(f"{YELLOW}Warning: Shell script '{filename}' is not executable. Attempting to run anyway...{RESET}")
             cmd = [interpreter, abs_file_to_run] + script_args
        elif (os.name == 'nt' and ext in ['.exe', '.bat', '.cmd']) or \
             (os.name != 'nt' and os.access(abs_file_to_run, os.X_OK)):
            # Try direct execution for executables (.exe, .bat, .cmd on win, or +x on linux/mac)
            print(f"{YELLOW}Attempting direct execution of {filename}...{RESET}")
            cmd = [abs_file_to_run] + script_args
        else:
            supported = False
            print(f"{RED}Error: Unsupported or non-executable file type for 'run': {filename}{RESET}")
            print("Supported extensions: .py, .class, .lua, .js, .sh, .bash")
            print("Also attempts direct execution of files marked executable (+x) or .exe/.bat/.cmd on Windows.")
            return

        if supported:
            try:
                cmd_str = shlex.join(cmd)
            except AttributeError:
                cmd_str = ' '.join([shlex.quote(p) for p in cmd]) # Manual quoting for older Python
            print(f"Running: {cmd_str}")
            subprocess.run(cmd, check=True) # Let CalledProcessError handle failures

    except FileNotFoundError as e:
        print(f"{RED}Error: {e}{RESET}")
        print("Please ensure the required interpreter/executable is installed and in your system's PATH.")
    except PermissionError:
         print(f"{RED}Error: Permission denied to execute '{filename}' or its interpreter.{RESET}")
    except OSError as e: # Catch exec format errors etc.
         print(f"{RED}Error executing '{filename}': {e}{RESET}")
    except subprocess.CalledProcessError as e:
        # Error message now includes exit code, no need to print separately
        print(f"{RED}Error: Execution failed for '{filename}' (exit code {e.returncode}).{RESET}")
    except Exception as e:
        print(f"{RED}An unexpected error occurred while trying to run '{filename}': {e}{RESET}")


def cowsay(text_args):
    """Displays text using an embedded cowsay. Text wraps automatically.
    Usage: cowsay <text>"""
    if not text_args: text = "Moo?"
    else: text = " ".join(text_args)

    # Try to get terminal width for better wrapping/boxing
    DEFAULT_WIDTH = 40 # Default wrap width if terminal size unknown
    try:
        terminal_width = os.get_terminal_size().columns
        # Max width for text inside the box, leave space for borders `|  |`
        max_line_len = max(10, terminal_width - 6)
    except OSError:
        max_line_len = DEFAULT_WIDTH

    # Simple word wrapping
    lines = []
    current_line = ""
    for word in text.split():
        word_len = calculate_visual_width(word) # Use visual width
        current_len = calculate_visual_width(current_line)
        if not current_line:
            current_line = word
        elif current_len + word_len + 1 <= max_line_len:
            current_line += " " + word
        else:
            # Handle words longer than the line length
            if word_len > max_line_len:
                 if current_line: lines.append(current_line)
                 # Break long word (rudimentary)
                 # This part is tricky with visual width, stick to simple length break for now
                 lines.append(word[:max_line_len])
                 current_line = word[max_line_len:] # Start next line with rest of word
                 # Continue breaking if still too long (simple approach)
                 while len(current_line) > max_line_len:
                      lines.append(current_line[:max_line_len])
                      current_line = current_line[max_line_len:]
            else:
                lines.append(current_line)
                current_line = word
    if current_line: lines.append(current_line)
    if not lines: lines.append("") # Ensure at least one empty line if input was empty


    box_width = 0
    for line in lines:
        box_width = max(box_width, calculate_visual_width(line))

    message = ""
    if len(lines) == 1:
        # Single line message: < message >
        message = f"< {lines[0]} >"
        top_border = f" {'_' * (box_width + 2)} "
        bottom_border = f" {'-' * (box_width + 2)} "
    else:
        # Multi-line message: /---\ | msg | \---/
        top_border = f" /{'-' * (box_width + 2)}\\"
        message_lines = []
        for line in lines:
            visual_len = calculate_visual_width(line)
            padding = " " * (box_width - visual_len) # Pad based on visual difference
            message_lines.append(f"| {line}{padding} |")
        message = "\n ".join(message_lines) # Add space for alignment with cow's head
        bottom_border = f" \\{'-' * (box_width + 2)}/"

    # Cow ASCII art
    cow = f"""
{top_border}
 {message}
{bottom_border}
        \   ^__^
         \  (oo)\_______
            (__)\       )\/\\
                ||----w |
                ||     ||
"""
    print(cow)


# --- Application Installation and Management ---

def parse_app_conf_content(content):
    """Parses the content of an app.conf file string."""
    conf_data = {}
    try:
        for line_num, line in enumerate(content.splitlines(), 1):
            line = line.strip()
            if not line or line.startswith('#'): continue
            # Allow comments after value using '#'
            line = line.split('#', 1)[0].strip()
            if not line: continue # Line was just a comment

            if ":" in line:
                key, value = line.split(":", 1)
                conf_data[key.strip().lower()] = value.strip()
            else:
                 print(f"{YELLOW}Warning: Malformed line {line_num} in app config content (missing ':'). Ignored: '{line}'{RESET}")
    except Exception as e:
        print(f"{RED}Error parsing app.conf content: {e}{RESET}")
        return None
    return conf_data


def install(args):
    """Installs an app using an installer config URL or a repo name.
    The installer config specifies URLs for the final app.conf and scripts.
    Usage: install <url_or_name>"""
    if not args:
        print("Usage: install <url_or_name>")
        print("Use 'repo list' to see available names.")
        return
    identifier = args[0]

    installer_config_url = ""
    # Resolve identifier to URL
    if identifier in APP_REPOSITORY:
        installer_config_url = APP_REPOSITORY[identifier]
        print(f"Found '{identifier}' in repository. Using installer config URL: {installer_config_url}")
    else:
        # Assume it's a direct URL
        installer_config_url = identifier
        parsed_url = urlparse(installer_config_url)
        if not parsed_url.scheme in ['http', 'https'] or not parsed_url.netloc:
             # Could check if it looks like a path to a local installer file too?
             # if os.path.isfile(identifier): ... handle local install config ...
             # else:
             print(f"{RED}Error: Invalid URL or unknown app name: {identifier}{RESET}")
             return
        print(f"Using direct installer config URL: {installer_config_url}")

    # --- Step 1: Fetch and Parse the *Installer* Config ---
    installer_data = {}
    optional_urls = []
    try:
        print(f"Fetching installer config from: {installer_config_url} ... ", end="", flush=True)
        # Use same headers as download_file
        headers = {'User-Agent': f'MyPythonOS Installer/1.4 ({platform.system()}; Python/{platform.python_version()})'}
        installer_resp = requests.get(installer_config_url, headers=headers, timeout=20, allow_redirects=True)
        installer_resp.raise_for_status()
        print(f"{GREEN}Success{RESET}")

        # Parse the installer config (folder-name, conf-url, script-url, optional-url)
        for line_num, line in enumerate(installer_resp.text.splitlines(), 1):
            line = line.strip()
            if not line or line.startswith('#'): continue
            line = line.split('#', 1)[0].strip() # Allow comments
            if not line: continue

            if ":" in line:
                key, value = line.split(":", 1)
                key, value = key.strip().lower(), value.strip()
                if not value:
                     print(f"{YELLOW}Warning: Empty value for key '{key}' at line {line_num} in installer config. Skipping.{RESET}")
                     continue

                if key == "optional-url":
                    optional_urls.append(value) # Allow multiple optional URLs
                elif key in ["folder-name", "conf-url", "script-url"]:
                    if key in installer_data:
                         print(f"{YELLOW}Warning: Duplicate key '{key}' at line {line_num} in installer config. Using last value.{RESET}")
                    installer_data[key] = value
                else:
                    print(f"{YELLOW}Warning: Unknown key '{key}' at line {line_num} in installer config. Ignored.{RESET}")
            else:
                print(f"{YELLOW}Warning: Malformed line {line_num} in installer config (missing ':'). Ignored: '{line}'{RESET}")

        # Validate required keys from installer config
        folder_name = installer_data.get("folder-name")
        conf_url = installer_data.get("conf-url")
        script_url = installer_data.get("script-url")

        if not folder_name or not conf_url or not script_url:
            missing = [k for k in ['folder-name', 'conf-url', 'script-url'] if not installer_data.get(k)]
            print(f"{RED}Error: Invalid installer configuration from {installer_config_url}. Missing: {', '.join(missing)}{RESET}")
            return

    except requests.exceptions.RequestException as e:
        print(f"{RED}\nError: Failed to fetch installer configuration: {e}{RESET}")
        return
    except Exception as e:
        print(f"{RED}\nAn unexpected error occurred while processing installer config: {e}{RESET}")
        return


    # --- Step 2: Fetch and Parse the *Final app.conf* Content ---
    local_conf_content = None
    app_name = None
    command_name = None
    version = "N/A"
    main_script_filename = None
    try:
        print(f"Fetching final app config from: {conf_url} ... ", end="", flush=True)
        headers = {'User-Agent': f'MyPythonOS Installer/1.4 ({platform.system()}; Python/{platform.python_version()})'}
        conf_resp = requests.get(conf_url, headers=headers, timeout=20, allow_redirects=True)
        conf_resp.raise_for_status()
        local_conf_content = conf_resp.text # Store the content to write later
        print(f"{GREEN}Success{RESET}")

        # Parse the content to get app details for validation/conflict check
        app_conf_data = parse_app_conf_content(local_conf_content)
        if not app_conf_data:
             print(f"{RED}Error: Could not parse the final app config content fetched from {conf_url}{RESET}")
             return

        app_name = app_conf_data.get("name")
        command_name = app_conf_data.get("command", app_name) # Default command to name if missing
        version = app_conf_data.get("version", "N/A")
        main_script_filename = app_conf_data.get("file")

        if not app_name or not command_name or not main_script_filename:
             missing = []
             if not app_name: missing.append("'name'")
             # If command was missing but name existed, command_name is now == app_name
             if not command_name: missing.append("'command'") # Should not happen now
             if not main_script_filename: missing.append("'file'")
             print(f"{RED}Error: The final app config from {conf_url} is invalid. Missing: {', '.join(missing)}{RESET}")
             return

        # Verify script filename consistency more robustly
        try:
            script_url_filename = os.path.basename(urlparse(script_url).path)
            if not script_url_filename: raise ValueError("No filename in script URL path")
        except Exception:
             print(f"{YELLOW}Warning: Could not reliably determine filename from script-url: {script_url}{RESET}")
             script_url_filename = None # Cannot compare

        if script_url_filename and script_url_filename != main_script_filename:
             print(f"{YELLOW}Warning: Script filename from script-url ('{script_url_filename}')")
             print(f"         does not match 'file:' in app.conf ('{main_script_filename}').")
             print(f"         Using '{main_script_filename}' from app.conf for saving.{RESET}")


    except requests.exceptions.RequestException as e:
        print(f"{RED}\nError: Failed to fetch final app configuration from {conf_url}: {e}{RESET}")
        return
    except Exception as e:
        print(f"{RED}\nAn unexpected error occurred while processing final app config: {e}{RESET}")
        return

    # --- Step 3: Conflict Check and Directory Preparation ---
    # Define built-ins explicitly for check
    built_in_commands = [
        f.__name__ for f in [ls, delf, deld, cd, pwd, mkdir, touch, move, help, clear, edit, javac,
                             run, download, install, repo, cowsay, delpanic, neofetch]
    ]
    if command_name in built_in_commands:
         print(f"{RED}Error: Command '{command_name}' (from app '{app_name}') conflicts with a built-in OS command. Installation aborted.{RESET}")
         return
    if command_name in INSTALLED_APPS:
        existing_app = INSTALLED_APPS[command_name]['name']
        print(f"{RED}Error: Command '{command_name}' is already used by application '{existing_app}'. Installation aborted.{RESET}")
        return

    # Validate folder name (prevent path traversal etc.)
    if ".." in folder_name or "/" in folder_name or "\\" in folder_name or folder_name.startswith('.'):
        print(f"{RED}Error: Invalid folder name '{folder_name}' specified in installer config. Installation aborted.{RESET}")
        return

    # App dir location depends on the structure defined in installer config
    # Assume the folder_name defines the final directory relative to APPLICATIONS_DIR
    # This means the installer controls if it goes into `applications/app_name` or `applications/category/app_name`
    # Example: folder_name="my_app" -> installs to applications/my_app
    # Example: folder_name="utilities/my_app" -> installs to applications/utilities/my_app
    app_dir = os.path.abspath(os.path.join(APPLICATIONS_DIR, folder_name))
    app_dir_rel = os.path.relpath(app_dir, ROOT_PATH) # For display

    if os.path.exists(app_dir):
        overwrite = input(f"{YELLOW}Application directory '{app_dir_rel}' already exists. Overwrite? (y/N): {RESET}").lower()
        if overwrite == 'y':
            print(f"Removing existing directory: {app_dir_rel}")
            try:
                shutil.rmtree(app_dir)
            except OSError as e:
                print(f"{RED}Error removing existing directory: {e}. Installation aborted.{RESET}")
                return
        else:
            print("Installation aborted by user.")
            return
    try:
        # Make parent directories if needed (e.g., for category/app_name)
        os.makedirs(app_dir, exist_ok=True)
        print(f"Created application directory: {app_dir_rel}")
    except OSError as e:
        print(f"{RED}Error creating application directory '{app_dir_rel}': {e}. Installation aborted.{RESET}")
        return

    # --- Step 4: Download and Save Files ---
    success = True
    files_to_download = []
    # Main script
    script_filepath = os.path.join(app_dir, main_script_filename)
    files_to_download.append({"url": script_url, "path": script_filepath, "optional": False})
    # Optional scripts
    for opt_url in optional_urls:
        try:
             opt_filename = os.path.basename(urlparse(opt_url).path)
             if not opt_filename:
                 print(f"{YELLOW}Warning: Could not determine filename for optional URL: {opt_url}. Skipping.{RESET}")
                 continue
             # Basic validation for optional file names too
             if ".." in opt_filename or "/" in opt_filename or "\\" in opt_filename or opt_filename.startswith('.'):
                  print(f"{YELLOW}Warning: Skipping optional URL with potentially unsafe filename: {opt_filename}{RESET}")
                  continue
             opt_filepath = os.path.join(app_dir, opt_filename)
             files_to_download.append({"url": opt_url, "path": opt_filepath, "optional": True})
        except Exception as e:
             print(f"{YELLOW}Warning: Error processing optional URL '{opt_url}': {e}. Skipping.{RESET}")

    # Download loop
    downloaded_files = []
    for item in files_to_download:
        if download_file(item["url"], item["path"]):
            downloaded_files.append(item["path"]) # Track successful downloads for cleanup
        else:
            if item["optional"]:
                print(f"{YELLOW}Warning: Failed to download OPTIONAL file: {os.path.basename(item['path'])}. Continuing installation.{RESET}")
            else:
                print(f"{RED}Failed to download required file: {os.path.basename(item['path'])}. Installation aborted.{RESET}")
                success = False
                break # Stop downloading required files on failure

    # Save the final app.conf (do this *after* successful downloads)
    if success:
        conf_filepath = os.path.join(app_dir, "app.conf")
        try:
            with open(conf_filepath, "w", encoding='utf-8') as f:
                f.write(local_conf_content)
            print(f"Saved configuration file: {os.path.basename(conf_filepath)}")
            downloaded_files.append(conf_filepath) # Add conf file to cleanup list
        except OSError as e:
            print(f"{RED}Error saving configuration file: {e}. Installation aborted.{RESET}")
            success = False

    # --- Step 5: Cleanup or Finalize ---
    if not success:
        print(f"{RED}Installation failed. Cleaning up...{RESET}")
        try:
            # Safer to just remove the whole app dir we created/overwrote
            if os.path.exists(app_dir):
                shutil.rmtree(app_dir)
                print(f"Removed incomplete application directory: {app_dir_rel}")
        except OSError as e:
            print(f"{RED}Error during cleanup: {e}{RESET}")
        return

    # Finalize: Make script executable (if needed) and reload apps
    print(f"{GREEN}Successfully installed application '{app_name}' (command: {command_name} v{version}) into '{app_dir_rel}'.{RESET}")
    main_script_path = os.path.join(app_dir, main_script_filename)
    # Make the main script executable on non-Windows
    if os.path.exists(main_script_path) and os.name != 'nt':
         try:
             current_mode = os.stat(main_script_path).st_mode
             # Ensure user has execute permission (u+x)
             os.chmod(main_script_path, current_mode | 0o100)
             print(f"Made '{main_script_filename}' executable.")
         except OSError as e:
             print(f"{YELLOW}Warning: Could not make script '{main_script_filename}' executable: {e}{RESET}")

    load_applications() # Reload applications


def setup_app(app_dir):
    """Reads app.conf and registers an application command. app_dir should be absolute."""
    conf_file = os.path.join(app_dir, "app.conf")
    app_dir_rel = os.path.relpath(app_dir, APPLICATIONS_DIR) # Relative to 'applications' for messages

    # This function should ONLY be called with directories confirmed to exist
    # and contain app.conf by load_applications. So no need to check conf_file exists here.

    try:
        # Read and parse the app.conf content
        with open(conf_file, "r", encoding='utf-8') as f:
             content = f.read()
        conf_data = parse_app_conf_content(content)

        if not conf_data:
             print(f"{YELLOW}Warning: Could not parse app.conf in '{app_dir_rel}'. Skipping.{RESET}")
             return

        name = conf_data.get("name")
        command = conf_data.get("command", name) # Default command to name
        version = conf_data.get("version", "N/A")
        file_to_run = conf_data.get("file")

        if not name or not command or not file_to_run:
            print(f"{YELLOW}Warning: Invalid app.conf in '{app_dir_rel}'. Missing 'name', 'command', or 'file'. Skipping.{RESET}")
            return

        # Use absolute paths for reliability
        script_path = os.path.join(app_dir, file_to_run) # app_dir is already absolute

        if not os.path.exists(script_path):
            print(f"{YELLOW}Warning: Script '{file_to_run}' not found in '{app_dir_rel}' for app '{name}'. Skipping.{RESET}")
            return

        # Conflict check (re-check during loading)
        built_in_commands = [
            f.__name__ for f in [ls, delf, deld, cd, pwd, mkdir, touch, move, help, clear, edit, javac,
                                 run, download, install, repo, cowsay, delpanic, neofetch]
        ]
        if command in built_in_commands:
            print(f"{YELLOW}Warning: Command '{command}' (app '{name}' in '{app_dir_rel}') conflicts with built-in. Skipping app.{RESET}")
            return
        if command in INSTALLED_APPS:
            existing_app_info = INSTALLED_APPS[command]
            existing_app_rel_path = os.path.relpath(existing_app_info['app_dir'], APPLICATIONS_DIR)
            print(f"{YELLOW}Warning: Command '{command}' conflict: App '{name}' in '{app_dir_rel}' vs existing app '{existing_app_info['name']}' in '{existing_app_rel_path}'. Skipping '{name}'.{RESET}")
            return

        INSTALLED_APPS[command] = {
            "name": name,
            "script": script_path, # Store absolute path
            "version": version,
            "app_dir": app_dir # Store absolute path
        }
        # print(f"DEBUG: Registered app '{name}' (command '{command}') from '{app_dir_rel}'") # Optional debug

    except OSError as e:
         print(f"{RED}Error reading configuration for app in '{app_dir_rel}': {e}{RESET}")
    except Exception as e:
        print(f"{RED}Error setting up app from '{app_dir_rel}': {e}{RESET}")
        traceback.print_exc()


def load_applications():
    """
    Loads applications from the applications directory.
    Searches for directories containing 'app.conf' directly within APPLICATIONS_DIR
    and one level deeper (e.g., APPLICATIONS_DIR/category/app_dir/app.conf).
    """
    global INSTALLED_APPS
    INSTALLED_APPS.clear() # Clear before loading

    apps_dir_abs = os.path.abspath(APPLICATIONS_DIR) # Ensure we use absolute path

    if not os.path.exists(apps_dir_abs):
        try:
            os.makedirs(apps_dir_abs)
            print(f"Created 'applications' directory: {apps_dir_abs}")
            return # Nothing to load yet
        except OSError as e:
            print(f"{RED}Error: Could not create 'applications' directory: {e}{RESET}")
            return

    app_count = 0
    processed_dirs = set() # Keep track of application directories already processed

    try:
        # Iterate through items directly in APPLICATIONS_DIR (Level 1 Items)
        for item_name_l1 in os.listdir(apps_dir_abs):
            path_l1 = os.path.abspath(os.path.join(apps_dir_abs, item_name_l1))

            # Consider only directories at level 1
            if os.path.isdir(path_l1):

                # --- Check if the Level 1 directory ITSELF is an app ---
                conf_file_l1 = os.path.join(path_l1, "app.conf")
                if os.path.isfile(conf_file_l1):
                    if path_l1 not in processed_dirs:
                        # print(f"DEBUG: Checking Level 1 App: {os.path.relpath(path_l1, apps_dir_abs)}") # Optional Debug
                        original_app_count = len(INSTALLED_APPS)
                        setup_app(path_l1) # Process this directory as an app
                        if len(INSTALLED_APPS) > original_app_count:
                            app_count += 1
                        processed_dirs.add(path_l1) # Mark as processed

                # --- Check for app directories INSIDE the Level 1 directory (Level 2) ---
                # We look inside every level 1 directory, regardless of whether it was an app itself or not.
                try:
                    for item_name_l2 in os.listdir(path_l1):
                        path_l2 = os.path.abspath(os.path.join(path_l1, item_name_l2))

                        # Consider only directories at level 2
                        if os.path.isdir(path_l2):
                            conf_file_l2 = os.path.join(path_l2, "app.conf")
                            if os.path.isfile(conf_file_l2):
                                if path_l2 not in processed_dirs:
                                     # print(f"DEBUG: Checking Level 2 App: {os.path.relpath(path_l2, apps_dir_abs)}") # Optional Debug
                                     original_app_count = len(INSTALLED_APPS)
                                     setup_app(path_l2) # Process this directory as an app
                                     if len(INSTALLED_APPS) > original_app_count:
                                         app_count += 1
                                     processed_dirs.add(path_l2) # Mark as processed

                except OSError as e_inner:
                     # Error listing inside a level 1 directory (e.g., permission denied)
                     print(f"{YELLOW}Warning: Could not list contents of '{os.path.basename(path_l1)}': {e_inner}{RESET}")
                     continue # Continue to the next level 1 item


    except OSError as e_outer:
         print(f"{RED}Error listing applications directory '{apps_dir_abs}': {e_outer}{RESET}")
    except Exception as e:
         print(f"{RED}Unexpected error loading applications: {e}{RESET}")
         traceback.print_exc() # Print traceback for unexpected errors


    if app_count > 0:
        print(f"{GREEN}Loaded {app_count} applications.{RESET}")


def app(command, args):
    """Runs an installed application command with arguments. Assumes command exists in INSTALLED_APPS."""
    if command not in INSTALLED_APPS:
         print(f"{RED}Internal Error: Attempted to run app '{command}' but it's not loaded.{RESET}")
         return

    app_info = INSTALLED_APPS[command]
    script_file = app_info["script"] # Absolute path
    app_dir = app_info["app_dir"]   # Absolute path
    app_dir_rel = os.path.relpath(app_dir, APPLICATIONS_DIR) # Relative for messages

    interpreter = None
    cmd = []
    ext = os.path.splitext(script_file)[1].lower()

    original_cwd = os.getcwd() # Store CWD before changing
    try:
         # Change CWD to the app's directory *before* trying to run it
         # This makes relative paths inside the app script work correctly.
         os.chdir(app_dir)
         print(f"Running '{app_info['name']}' (v{app_info['version']}) from '{app_dir_rel}/'...")

         supported = True
         if ext == ".py":
             if shutil.which("python3"): interpreter = "python3"
             elif shutil.which("python"): interpreter = "python"
             else: raise FileNotFoundError("No Python interpreter found for app")
             cmd = [interpreter, script_file] + args
         elif ext == ".js":
             if not shutil.which("node"): raise FileNotFoundError("Node.js interpreter 'node' not found for app")
             cmd = ["node", script_file] + args
         elif ext == ".lua":
             if not shutil.which("lua"): raise FileNotFoundError("Lua interpreter 'lua' not found for app")
             cmd = ["lua", script_file] + args
         elif ext in [".sh", ".bash"]:
             if shutil.which("bash"): interpreter = "bash"
             elif shutil.which("sh"): interpreter = "sh"
             else: raise FileNotFoundError("No Shell interpreter ('bash' or 'sh') found for app")
             if os.name != 'nt' and not os.access(script_file, os.X_OK):
                 print(f"{YELLOW}Warning: App script '{os.path.basename(script_file)}' is not executable. Trying anyway...{RESET}")
             cmd = [interpreter, script_file] + args
         elif (os.name == 'nt' and ext in ['.exe', '.bat', '.cmd']) or \
              (os.name != 'nt' and os.access(script_file, os.X_OK)):
             # Try direct execution for executables
             print(f"{YELLOW}Attempting direct execution of app file {os.path.basename(script_file)}...{RESET}")
             cmd = [script_file] + args
         else:
             supported = False
             print(f"{RED}Error: Cannot run app '{app_info['name']}'. Unsupported or non-executable file type: {os.path.basename(script_file)}{RESET}")

         # Execute if supported
         if supported:
             try:
                 cmd_str = shlex.join(cmd)
             except AttributeError:
                 cmd_str = ' '.join([shlex.quote(p) for p in cmd]) # Fallback for older python
             print(f"Executing: {cmd_str}")
             subprocess.run(cmd, check=True) # Let CalledProcessError handle fail

    except FileNotFoundError as e:
        print(f"{RED}Error running app '{app_info['name']}': Interpreter or script not found. {e}{RESET}")
    except PermissionError as e:
        print(f"{RED}Error running app '{app_info['name']}': Permission denied. {e}{RESET}")
    except OSError as e: # Handle other OS errors like "Exec format error"
        print(f"{RED}Error executing application '{app_info['name']}': {e}{RESET}")
    except subprocess.CalledProcessError as e:
        print(f"{YELLOW}Application '{app_info['name']}' exited with non-zero status ({e.returncode}).{RESET}")
    except Exception as e:
        print(f"{RED}An unexpected error occurred while running app '{command}': {e}{RESET}")
        traceback.print_exc() # Print traceback for app errors too
    finally:
         # ALWAYS change back to original CWD
         try:
             os.chdir(original_cwd)
         except OSError as cd_err:
             print(f"{RED}Error: Could not change back to original directory '{os.path.relpath(original_cwd, ROOT_PATH)}': {cd_err}{RESET}")
             try:
                 os.chdir(ROOT_PATH)
                 print(f"{YELLOW}Changed directory to root.{RESET}")
             except OSError as root_err:
                 print(f"{RED}FATAL: Could not change directory to root. CWD state unknown.{RESET}")


def repo(args):
    """Manages the application repository (repo.txt).
    Usage: repo list | update [<url>] | add <name> <url> | remove <name>"""
    if not args:
        print("Usage: repo list | update [<url>] | add <name> <url> | remove <name>")
        print(f"Default update URL: {DEFAULT_REPO_URL}")
        return

    subcommand = args[0].lower()
    repo_file_path = os.path.abspath(REPO_FILE) # Use absolute path
    repo_file_basename = os.path.basename(repo_file_path)

    if subcommand == "list":
        if not APP_REPOSITORY:
            print("Repository is empty or not loaded.")
            print(f"Try 'repo update' or manually edit '{repo_file_basename}'.")
            return
        print(f"--- Application Repository ('{repo_file_basename}') ---")
        if not APP_REPOSITORY: # Check again after msg
            print("  (empty)")
        else:
            max_name_len = max((len(name) for name in APP_REPOSITORY.keys()), default=0)
            for name, url in sorted(APP_REPOSITORY.items()):
                print(f"  {name:<{max_name_len}} : {url}")
            print(f"--- {len(APP_REPOSITORY)} entries ---")

    elif subcommand == "update":
        url_to_update = DEFAULT_REPO_URL
        if len(args) > 1:
            url_to_update = args[1]
            parsed_url = urlparse(url_to_update)
            if not parsed_url.scheme in ['http', 'https'] or not parsed_url.netloc:
                 print(f"{RED}Error: Invalid URL provided: {url_to_update}{RESET}")
                 return
        print(f"Attempting to update repository from: {url_to_update}")
        if download_file(url_to_update, repo_file_path):
            print(f"{GREEN}Repository file '{repo_file_basename}' updated successfully. Reloading...{RESET}")
            load_repository() # Reload changes into memory
        else:
            print(f"{RED}Failed to update repository file from the URL.{RESET}")

    elif subcommand == "add":
        if len(args) != 3: print("Usage: repo add <name> <url>"); return
        name, url = args[1], args[2]
        # Basic validation
        if not name or ":" in name or name.startswith('#') or ' ' in name:
            print(f"{RED}Error: Invalid name '{name}'. Cannot contain ':', '#', or spaces.{RESET}"); return
        parsed_url = urlparse(url);
        if not parsed_url.scheme in ['http', 'https'] or not parsed_url.netloc:
            print(f"{RED}Error: Invalid URL '{url}'. Must be http or https.{RESET}"); return

        # Check existing entry (case-sensitive)
        entry_exists = name in APP_REPOSITORY
        current_url = APP_REPOSITORY.get(name)

        if entry_exists and current_url == url:
             print(f"{YELLOW}Entry '{name}' already exists with the same URL. No changes made.{RESET}")
             return
        elif entry_exists:
             print(f"{YELLOW}Warning: Name '{name}' already exists with URL: {current_url}{RESET}")
             overwrite = input(f"Overwrite with new URL '{url}'? (y/N): ").lower()
             if overwrite != 'y': print("Add operation cancelled."); return

        # Update in memory first
        APP_REPOSITORY[name] = url

        # Write back to file atomically
        temp_repo_file = repo_file_path + ".tmp"
        try:
            with open(temp_repo_file, "w", encoding='utf-8') as f:
                # Write comments/header? Optional.
                # f.write("# MyPythonOS Application Repository\n")
                for n, u in sorted(APP_REPOSITORY.items()):
                    f.write(f"{n}\n{u}\n") # Ensure newline at end
            shutil.move(temp_repo_file, repo_file_path) # Atomic replace
            print(f"{GREEN}{'Updated' if entry_exists else 'Added'} '{name}' in repository file '{repo_file_basename}'.{RESET}")
        except (OSError, IOError, shutil.Error) as e:
            print(f"{RED}Error writing updated repository file: {e}{RESET}")
            print(f"{YELLOW}Reverting in-memory change...{RESET}")
            # Revert the change in memory if file write failed
            if entry_exists: APP_REPOSITORY[name] = current_url # Restore old URL
            else:
                if name in APP_REPOSITORY: # Double check before deleting
                    del APP_REPOSITORY[name]


    elif subcommand == "remove":
        if len(args) != 2: print("Usage: repo remove <name>"); return
        name = args[1]
        if name not in APP_REPOSITORY: print(f"{RED}Error: Name '{name}' not found in repository.{RESET}"); return

        removed_url = APP_REPOSITORY[name] # Store for potential revert
        print(f"Removing '{name}' ({removed_url}) ...")

        # Update in memory first
        del APP_REPOSITORY[name]

        # Write back to file atomically
        temp_repo_file = repo_file_path + ".tmp"
        try:
            with open(temp_repo_file, "w", encoding='utf-8') as f:
                 if APP_REPOSITORY: # Check if repo is now empty
                     # f.write("# MyPythonOS Application Repository\n")
                     for n, u in sorted(APP_REPOSITORY.items()):
                         f.write(f"{n}\n{u}\n")
                 # If empty, the temp file will be empty, replacing the old one
            shutil.move(temp_repo_file, repo_file_path) # Atomic replace
            print(f"{GREEN}Removed '{name}' from repository file '{repo_file_basename}'.{RESET}")
        except (OSError, IOError, shutil.Error) as e:
            print(f"{RED}Error writing updated repository file: {e}{RESET}")
            print(f"{YELLOW}Reverting in-memory change...{RESET}")
            # Revert the change in memory
            APP_REPOSITORY[name] = removed_url


    else:
        print(f"{RED}Error: Unknown repo subcommand '{subcommand}'.{RESET}")
        print("Usage: repo list | update [<url>] | add <name> <url> | remove <name>")


# --- Panic Command ---

def delpanic():
    """Deletes most files/dirs in root, except critical ones. Requires confirmation."""
    # Define preserved items RELATIVE to ROOT_PATH for clarity
    preserve_relative = [
        os.path.basename(MAIN_SCRIPT),
        os.path.basename(USER_CONFIG_FILE),
        os.path.basename(REPO_FILE),
        os.path.basename(APPLICATIONS_DIR)
    ]
    # Calculate absolute paths for comparison
    preserve_absolute = [os.path.abspath(os.path.join(ROOT_PATH, p)) for p in preserve_relative]
    # Also preserve the root path itself! (Though shouldn't be deletable by item loop)
    # preserve_absolute.append(os.path.abspath(ROOT_PATH)) # Not strictly needed

    sentences = [
        "The quick brown fox jumps over the lazy dog.",
        "Never gonna give you up, never gonna let you down.",
        "All your base are belong to us.",
        "A penny saved is a penny earned.",
        "Early to bed and early to rise makes a man healthy, wealthy and wise.",
        "Winter is coming.", "I solemnly swear that I am up to no good.",
        "With great power comes great responsibility.", "This command will delete many files."
    ]
    num_confirm = min(3, len(sentences))
    if num_confirm < 3: print(f"{YELLOW}Warning: Not enough confirmation sentences available.{RESET}")
    try: chosen_sentences = random.sample(sentences, num_confirm)
    except ValueError: print(f"{RED}Error selecting confirmation sentences.{RESET}"); return

    print(f"{RED}--- WARNING: DELPANIC INITIATED ---{RESET}")
    print(f"This command will attempt to delete MOST files and directories within: '{ROOT_PATH}'")
    print(f"EXCEPT for: {', '.join(preserve_relative)}")
    print(f"{RED}This action is EXTREMELY DESTRUCTIVE and likely IRREVERSIBLE.{RESET}")
    print(f"{YELLOW}To confirm, please type the following {num_confirm} sentences exactly (case-sensitive):{RESET}")
    for i, sentence in enumerate(chosen_sentences): print(f"  {i + 1}: {sentence}")

    for i in range(num_confirm):
        try:
            user_input = input(f"Sentence {i + 1}/{num_confirm}: ").strip()
            # Exact match required
            if user_input != chosen_sentences[i]:
                print(f"{RED}Confirmation failed. Input did not match. Aborting DELPANIC.{RESET}"); return
        except (EOFError, KeyboardInterrupt):
            print(f"\n{RED}Confirmation aborted by user. Aborting DELPANIC.{RESET}"); return

    print(f"{GREEN}Confirmation successful. Proceeding with DELPANIC in 3 seconds... (Ctrl+C to abort){RESET}")
    try:
        time.sleep(3)
    except KeyboardInterrupt:
        print(f"\n{RED}DELPANIC aborted by user during final countdown.{RESET}"); return

    print(f"{RED}--- EXECUTING DELPANIC ---{RESET}")
    deleted_count, error_count = 0, 0
    items_to_process = []
    try:
        # First, list items to process to avoid issues if listing fails mid-deletion
        items_to_process = os.listdir(ROOT_PATH)
    except OSError as e:
        print(f"{RED}Fatal Error listing directory {ROOT_PATH}: {e}{RESET}")
        print(f"{RED}DELPANIC aborted before deleting anything.{RESET}")
        return

    num_preserved_found = 0
    for item_name in items_to_process:
            item_path_abs = os.path.abspath(os.path.join(ROOT_PATH, item_name))

            # Check against preservation list
            if item_path_abs in preserve_absolute:
                print(f"Skipping preserved: {item_name}")
                num_preserved_found += 1
                continue

            # Attempt deletion
            try:
                if os.path.isfile(item_path_abs) or os.path.islink(item_path_abs): # Delete files and links
                    print(f"Deleting file/link: {item_name} ... ", end="", flush=True)
                    os.remove(item_path_abs)
                    print(f"{GREEN}OK{RESET}"); deleted_count += 1
                elif os.path.isdir(item_path_abs):
                    print(f"Deleting directory: {item_name} ... ", end="", flush=True)
                    shutil.rmtree(item_path_abs)
                    print(f"{GREEN}OK{RESET}"); deleted_count += 1
                else:
                    print(f"{YELLOW}Skipping unknown type: {item_name}{RESET}")
            except Exception as e:
                print(f"{RED}ERROR deleting '{item_name}': {e}{RESET}"); error_count += 1


    print(f"{GREEN}--- DELPANIC Complete ---{RESET}")
    print(f"Items attempted for deletion (excluding preserved): {len(items_to_process) - num_preserved_found}") # Correct count display
    print(f"Items successfully deleted: {deleted_count}")
    if error_count > 0: print(f"{RED}Errors occurred during deletion: {error_count}{RESET}")
    print(f"{YELLOW}You may need to restart the OS.{RESET}")


# --- Main Loop ---

def get_prompt(username, hostname):
    """Generates the custom prompt showing user@host:path $."""
    try:
        # Ensure CWD is valid, reset to root if not
        try:
            cwd = os.getcwd()
            # Check if cwd actually exists (might be deleted externally)
            if not os.path.exists(cwd):
                raise FileNotFoundError("Current working directory does not exist")
        except FileNotFoundError:
            print(f"\n{YELLOW}Warning: Current working directory lost or invalid. Returning to root.{RESET}")
            os.chdir(ROOT_PATH)
            cwd = ROOT_PATH
        except OSError as e:
             print(f"\n{RED}Error checking current directory: {e}. Returning to root.{RESET}")
             try:
                 os.chdir(ROOT_PATH)
             except OSError as root_e:
                 print(f"{RED}FATAL: Could not change to root directory '{ROOT_PATH}': {root_e}. Exiting.{RESET}")
                 exit(1) # Critical error, exit OS
             cwd = ROOT_PATH


        # Generate display path relative to ROOT_PATH
        display_path = ""
        root_path_abs = os.path.abspath(ROOT_PATH)
        cwd_abs = os.path.abspath(cwd)

        # Check if we are inside the root path
        if cwd_abs == root_path_abs:
            display_path = "~"
        elif cwd_abs.startswith(root_path_abs + os.sep): # Check if it starts with root + separator
             relative_path = os.path.relpath(cwd_abs, root_path_abs)
             display_path = f"~/{relative_path.replace(os.sep, '/')}"
        else:
            # If somehow outside the root (shouldn't happen with 'cd' checks, but defensive)
            print(f"\n{YELLOW}Warning: Current working directory '{cwd_abs}' is outside the root '{root_path_abs}'. Showing full path.{RESET}")
            display_path = cwd_abs # Show full absolute path

        return f"{GREEN}{username}@{hostname}{RESET}:{BLUE}{display_path}{RESET} $ "
    except OSError as e:
         # Handle potential errors during path manipulation or os.getcwd()
         print(f"\n{RED}Error getting prompt information: {e}. Using basic prompt.{RESET}")
         return f"{GREEN}{username}@{hostname}{RESET}:{RED}???{RESET} $ "


# --- Command Execution Helper ---

def run_single_command(cmd, args):
    """Executes a single parsed command. Returns False if exit command was issued."""
    # Map command strings to functions (more robust than giant elif)
    command_map = {
        "help": help,
        "clear": clear,
        "neofetch": neofetch,
        "ls": ls,
        "delf": delf,
        "deld": deld,
        "cd": cd,
        "pwd": pwd,
        "mkdir": mkdir,
        "touch": touch,
        "move": move,
        "edit": edit,
        "javac": javac,
        "run": run,
        "download": download,
        "install": install,
        "repo": repo,
        "cowsay": cowsay,
        "delpanic": delpanic,
        # Add other built-ins here
    }

    # Handle exit separately
    if cmd == "exit":
        print("Exiting MyPythonOS...")
        return False # Signal to exit main loop

    # Find the command function
    target_func = command_map.get(cmd)

    if target_func:
        # Built-in command found
        try:
            # Call the function. Most now expect args as a list.
            # Some built-ins might not take args (like clear, pwd, neofetch, help, delpanic)
            # Inspect signature to call correctly
            sig = inspect.signature(target_func)
            if not sig.parameters: # If function takes no parameters
                if args: # If args were provided anyway, show warning? Or just ignore? Ignore for now.
                    # print(f"{YELLOW}Warning: Command '{cmd}' does not accept arguments. Ignoring provided arguments.{RESET}")
                    pass
                target_func()
            else:
                target_func(args) # Pass args list

        except TypeError as te:
             # Handle cases where args were passed incorrectly (e.g., missing required arg for func)
             # This might indicate an issue with the function definition vs. call
             print(f"{RED}Error executing command '{cmd}': {te}{RESET}")
             print(f"{YELLOW}Usage might be incorrect. Try 'help {cmd}'.{RESET}")
             # print(f"DEBUG: Args received: {args}") # Optional debug
             # traceback.print_exc() # Optional debug
        except Exception as e:
             # Catch unexpected errors within the command function itself
             print(f"\n{RED}--- ERROR IN COMMAND '{cmd}' ---{RESET}")
             traceback.print_exc()
             print(f"{YELLOW}Command '{cmd}' failed to complete successfully.{RESET}")

    elif cmd in INSTALLED_APPS:
        # Installed application command
        try:
            app(cmd, args) # Call the app runner function
        except Exception as e:
             # Catch unexpected errors within the app runner function
             print(f"\n{RED}--- ERROR RUNNING APP '{cmd}' ---{RESET}")
             traceback.print_exc()
             print(f"{YELLOW}Application '{cmd}' failed.{RESET}")
    else:
        # Unknown command
        print(f"{RED}Command not found: {cmd}{RESET}")

    return True # Signal to continue main loop


def main():
    """Main loop of the simulated terminal."""
    global ROOT_PATH, username, hostname # Make username/hostname global for prompt

    # --- Initial Setup ---
    clear()
    print(f"Welcome to MyPythonOS!")
    # Ensure critical dirs exist *before* loading/saving configs
    try:
        # Ensure ROOT_PATH exists (though '.' usually does)
        # os.makedirs(ROOT_PATH, exist_ok=True) # Already done by abspath definition? Check. It should exist.
        # Ensure APPLICATIONS_DIR exists right away
        os.makedirs(APPLICATIONS_DIR, exist_ok=True)
    except OSError as e:
         print(f"{RED}Fatal Error: Could not create critical directory '{APPLICATIONS_DIR}': {e}{RESET}")
         return

    print(f"Root directory: {ROOT_PATH}")
    print(f"Type 'help' for commands, 'exit' to quit.")
    print(f"Commands can be chained with '|' (e.g., cmd1 | cmd2)")
    print("-" * 30)


    _uname, _hname = load_user_config()
    if not _uname or not _hname:
        print("Performing first-time user setup...")
        _uname, _hname = create_user_config()
        if not _uname or not _hname: # Handle error during creation
             print(f"{RED}Failed to create user config. Exiting.{RESET}")
             return
        print("-" * 30)
    username = _uname # Set global username
    hostname = _hname # Set global hostname

    # --- Repository Setup ---
    if not os.path.exists(REPO_FILE):
        print(f"Repository file '{os.path.basename(REPO_FILE)}' not found.")
        download_repo = ""
        try:
            download_repo = input(f"Download initial repository from default URL? (Y/n): ").lower()
        except (EOFError, KeyboardInterrupt):
            print("\nSkipping repository download.")
            download_repo = 'n' # Treat interrupt as 'no'

        if download_repo == "" or download_repo == "y":
            print(f"Attempting to download initial repository...")
            if download_file(DEFAULT_REPO_URL, REPO_FILE):
                print(f"{GREEN}Successfully downloaded initial repository.{RESET}")
            else:
                print(f"{YELLOW}Warning: Failed to download initial repository.{RESET}")
                print(f"You can try 'repo update' later or create '{os.path.basename(REPO_FILE)}' manually.")
        else:
            print(f"Skipping repository download. You can use 'repo update' later.")
        print("-" * 30)

    # --- Load Data ---
    load_repository()
    load_applications()
    print("-" * 30)

    # --- Set Initial Directory ---
    try:
        os.chdir(ROOT_PATH)
    except OSError as e:
        print(f"{RED}Fatal Error: Could not change to root directory '{ROOT_PATH}': {e}{RESET}")
        return

    # --- Command Loop ---
    running = True
    while running:
        try:
            prompt = get_prompt(username, hostname)
            command_line = input(prompt).strip()

            if not command_line: continue # Skip empty input

            # Split the input line into individual commands based on '|'
            # Handle potential empty strings if user types '||' or ends with '|'
            command_sequence = [cmd.strip() for cmd in command_line.split('|') if cmd.strip()]

            for single_command_str in command_sequence:
                # Use shlex to split the individual command string correctly,
                # handling quoted arguments.
                try:
                     parts = shlex.split(single_command_str)
                except ValueError as e:
                     # Handle broken quoting like unmatched quotes
                     print(f"{RED}Error parsing command segment '{single_command_str}': {e}{RESET}")
                     print(f"{YELLOW}Check quoting. Skipping this command segment.{RESET}")
                     continue # Skip this malformed part of the sequence

                if not parts: continue # Should not happen after initial strip, but safety first

                cmd = parts[0]
                args = parts[1:]

                # Execute the single command using the helper function
                running = run_single_command(cmd, args)
                if not running:
                    break # Exit the inner loop (command sequence) if 'exit' was called

            # The outer loop condition (while running) handles full exit

        except KeyboardInterrupt:
            print("\n^C") # Mimic shell interrupt, continue loop
        except EOFError:
            print("\nexit") # Mimic shell EOF (Ctrl+D)
            running = False # Set flag to exit loop cleanly
        except Exception as e:
            # Catch unexpected errors in the main loop logic itself
            print(f"\n{RED}--- UNEXPECTED OS ERROR ---{RESET}")
            print(f"{RED}A critical error occurred in the main loop:{RESET}")
            traceback.print_exc() # Print full traceback for debugging
            # Decide whether to try continuing or exit
            # For robustness, let's try to continue
            print(f"{YELLOW}Attempting to recover and continue...{RESET}")
            # Maybe reset CWD?
            try:
                os.chdir(ROOT_PATH)
                print(f"{YELLOW}Returned to root directory.{RESET}")
            except Exception as chdir_err:
                print(f"{RED}FATAL: Could not return to root directory after error: {chdir_err}. Exiting.{RESET}")
                running = False # Force exit if we can't even cd to root


if __name__ == "__main__":
    # Maybe add command-line args to MyPythonOS itself later?
    main()
    print(f"{ORANGE}MyPythonOS session ended.{RESET}")
