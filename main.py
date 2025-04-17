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
MAIN_SCRIPT = os.path.basename(__file__) # Name of current script

# --- Global State ---
INSTALLED_APPS = {}  # Dictionary to store installed applications info {command: {info}}
APP_REPOSITORY = {} # Dictionary to store name: url mappings from repo.txt {name: url}


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
    username = input("Enter username: ").strip()
    if not username: username = "user" # Default if empty
    hostname = input("Enter hostname: ").strip()
    if not hostname: hostname = "mypythos" # Default if empty

    config = {"username": username, "hostname": hostname}

    try:
        with open(USER_CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
        print(f"{GREEN}User configuration saved to user.json{RESET}")
        return username, hostname
    except OSError as e:
        print(f"{RED}Error: Could not create user.json: {e}{RESET}")
        return "user", "mypythos"  # Provide defaults in case of error

def load_repository():
    """Loads application repository information from repo.txt."""
    global APP_REPOSITORY
    APP_REPOSITORY.clear() # Clear previous entries before loading

    if not os.path.exists(REPO_FILE):
        print(f"{YELLOW}Repository file '{os.path.basename(REPO_FILE)}' not found or is empty.{RESET}")
        return

    try:
        with open(REPO_FILE, "r") as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith('#')] # Read non-empty, non-comment lines

        if not lines:
             print(f"{YELLOW}Repository file '{os.path.basename(REPO_FILE)}' is empty or contains only comments.{RESET}")
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

        print(f"{GREEN}Loaded {entries_loaded} entries from repository.{RESET}")

    except OSError as e:
        print(f"{RED}Error reading repository file '{os.path.basename(REPO_FILE)}': {e}{RESET}")
    except Exception as e:
        print(f"{RED}An unexpected error occurred while loading repository: {e}{RESET}")


# --- ASCII Art & Neofetch ---
NEOFETCH_ART = f"""
{RED}

                                     ####              #        ###     ###                                                         ##
          ########         #####  #########        ########  ######  #######                           #############          ##############
{ORANGE}          #########       ######  #########        ########  ######   ######                         #################       #################
          ##########      #  ###  #########        #### ###  ######  #######                        #########  # ######    # #####     #######
{YELLOW}           ##########     #######  #  #####        ##### ##  ######  ######                         #######     ########   #####         ##
          #### #######    #######     #####        ########  ######  ######                         #######       ## ###   #######
{GREEN}          ###### ######    ######  ## #####        ########  ######  ######                      #  #######       ######   ######### ##
          ######  ####### #######  ########        ########  ## ###   # ####     ###########  ####  #######      #######     ##############
{BLUE}          ######   ####### ######  ######          ##### ##  ######  ######     ###     ########    #######       #######       #############
           ######    ############  ########        ########  ######  ######                         #######      ### ####            ##########
{PURPLE}           ######     ###########  ########        ########  # ####  ## ###                         #######      ### ###                #######
           ######      ##########  #########     ##########  ######  #######                        #######      #######    ####        ####  #
{RED}           ######       #########  ########################  ######  #######                        #########  ########   ##########   #######
           ######        ########   #####  ####  # ########  ######  #######                         ##################     ##################
{ORANGE}           ######         #######    ###########   ########  #######  ######                           ##############         ##############
{ORANGE}                                      ###                                                                   ##                     ##


{RESET}""" # Add the reset AFTER the art


def neofetch():
    """Displays system information.
       Usage: neofetch"""
    print(NEOFETCH_ART)  # Print the ASCII art first

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


    print(f"""
        OS: {os_name}
        Kernel: {kernel}
        Architecture: {architecture}
        Python: {python_version}
        Files in CWD: {num_files}
        Dirs in CWD: {num_dirs}
        CWD: {cwd}
        """)


# --- Core File System Commands ---

def ls(args=None):
    """Lists files and directories in the current directory.
       Usage: ls [-l]"""
    try:
        detailed = False
        if args and args[0] == "-l":
            detailed = True

        items = sorted(os.listdir(os.getcwd())) # Sort alphabetically

        for item in items:
            try:
                 item_path = os.path.join(os.getcwd(), item)
                 if detailed:
                     if os.path.isfile(item_path):
                         file_type = "File"
                         size = os.path.getsize(item_path)
                         print(f"{file_type:<10} {size:>10} {item}")
                     elif os.path.isdir(item_path):
                         file_type = "Directory"
                         print(f"{file_type:<10} {'-':>10} {item}") # Use '-' for dir size
                     else:
                         file_type = "Other" # Symlinks, etc.
                         print(f"{file_type:<10} {'-':>10} {item}")
                 else:
                     # Colorized output
                     if os.path.isdir(item_path):
                         print(f"{BLUE}{item}{RESET}/") # Add slash for directories
                     elif os.path.isfile(item_path) and os.access(item_path, os.X_OK) and os.name != 'nt':
                          print(f"{GREEN}{item}{RESET}*") # Mark executable on Unix
                     elif os.path.isfile(item_path) and item.split('.')[-1] in ['exe', 'bat', 'com'] and os.name == 'nt':
                          print(f"{GREEN}{item}{RESET}*") # Mark executable on Windows
                     elif os.path.isfile(item_path):
                          print(item) # Regular file
                     else:
                          print(f"{ORANGE}{item}{RESET}") # Other types (symlinks, etc.)
            except OSError:
                 print(f"{RED}Error reading: {item}{RESET}") # Handle permission errors etc.

    except FileNotFoundError:
        print(f"{RED}Error: Current directory not found.{RESET}")
    except OSError as e:
        print(f"{RED}Error listing directory: {e}{RESET}")


def delf(filename):
    """Deletes a file.
       Usage: delf <filename>"""
    if not filename:
        print("Usage: delf <filename>")
        return
    try:
        # Prevent deleting critical files by name only (basic check)
        if filename in [os.path.basename(USER_CONFIG_FILE), os.path.basename(REPO_FILE), os.path.basename(MAIN_SCRIPT)]:
             print(f"{RED}Error: Cannot delete critical system file '{filename}' using delf.{RESET}")
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


def deld(dirname):
    """Deletes a directory (recursively).
       Usage: deld <directory>"""
    if not dirname:
        print("Usage: deld <directory>")
        return

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
        if os.path.commonpath([root_path_abs, target_path]) != root_path_abs and target_path == os.path.dirname(root_path_abs):
             print(f"{RED}Error: Cannot delete the parent directory of the OS root.{RESET}")
             return

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


def cd(directory=None):
    """Changes the current directory. 'cd ~' or 'cd' goes to root.
       Usage: cd [<directory> | ~]"""
    target_dir = ROOT_PATH # Default target is root

    if directory and directory != "~":
        target_dir = directory

    try:
        # Security: Prevent escaping the root using '..' excessively?
        # tentative_path = os.path.abspath(os.path.join(os.getcwd(), target_dir))
        # root_abs = os.path.abspath(ROOT_PATH)
        # if os.path.commonpath([root_abs, tentative_path]) != root_abs:
        #     print(f"{RED}Error: Cannot 'cd' outside the root directory '{ROOT_PATH}'.{RESET}")
        #     return

        os.chdir(target_dir)
        # Optionally print new pwd: pwd()
    except FileNotFoundError:
        print(f"{RED}Error: Directory not found: {target_dir}{RESET}")
    except NotADirectoryError:
        print(f"{RED}Error: Not a directory: {target_dir}{RESET}")
    except PermissionError:
         print(f"{RED}Error: Permission denied to change directory to '{target_dir}'.{RESET}")
    except OSError as e:
        print(f"{RED}Error changing directory: {e}{RESET}")


def pwd():
    """Prints the current working directory.
       Usage: pwd"""
    try:
        print(os.getcwd())
    except OSError as e:
        print(f"{RED}Error getting current directory: {e}{RESET}")


def mkdir(dirname):
    """Creates a new directory. Creates parent directories as needed.
       Usage: mkdir <directory>"""
    if not dirname:
        print("Usage: mkdir <directory>")
        return
    try:
        os.makedirs(dirname, exist_ok=True)
        print(f"Created directory: {dirname}")
    except PermissionError:
        print(f"{RED}Error: Permission denied to create directory '{dirname}'.{RESET}")
    except OSError as e:
        print(f"{RED}Error: Could not create directory '{dirname}': {e}{RESET}")


def touch(filename):
    """Creates a new empty file or updates its timestamp.
       Usage: touch <filename>"""
    if not filename:
        print("Usage: touch <filename>")
        return
    try:
        if os.path.isdir(filename):
             print(f"{RED}Error: '{filename}' is a directory.{RESET}")
             return

        parent_dir = os.path.dirname(filename)
        if parent_dir and not os.path.exists(parent_dir):
             os.makedirs(parent_dir)

        if os.path.exists(filename):
            os.utime(filename, None)
        else:
            with open(filename, 'a'): pass
        # No output on success for typical 'touch' behavior
    except PermissionError:
        print(f"{RED}Error: Permission denied for file operation on '{filename}'.{RESET}")
    except OSError as e:
        print(f"{RED}Error creating/updating file '{filename}': {e}{RESET}")


def move(source, destination):
    """Moves or renames a file or directory.
       Usage: move <source> <destination>"""
    if not source or not destination:
        print("Usage: move <source> <destination>")
        return
    try:
        # Prevent moving critical files/dirs to obscure places? Basic check.
        src_abs = os.path.abspath(source)
        critical_abs = [os.path.abspath(p) for p in [USER_CONFIG_FILE, REPO_FILE, MAIN_SCRIPT, APPLICATIONS_DIR]]
        if src_abs in critical_abs:
             print(f"{RED}Error: Cannot move critical system item '{source}' using move.{RESET}")
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
    for name, obj in globals().items():
        if callable(obj) and obj.__module__ == __name__ and not name.startswith("_") and name not in ["main", "load_user_config", "create_user_config", "get_prompt", "load_applications", "setup_app", "download_file", "load_repository", "parse_app_conf_content"]:
            commands[name] = obj

    for name, info in INSTALLED_APPS.items():
        if name not in commands:
            commands[name] = f"Runs the '{info['name']}' application (v{info['version']})"

    max_len = max(len(name) for name in commands.keys()) if commands else 0

    for name in sorted(commands.keys()):
        obj = commands[name]
        color = GREEN if callable(obj) else BLUE
        print(f"  {color}{name:<{max_len}}{RESET} : ", end="")

        if callable(obj):
            docstring = inspect.getdoc(obj)
            if docstring:
                lines = docstring.splitlines()
                print(lines[0]) # Print short description
                for line in lines[1:]: print(f"    {line.strip()}") # Print usage/details
            else: print("(No help available)")
        elif isinstance(obj, str): print(obj) # Print app description


def clear():
    """Clears the terminal screen.
       Usage: clear"""
    os.system('cls' if os.name == 'nt' else 'clear')


def edit(filename):
    """Edits a file using nano (if available), creates if non-existent.
       Usage: edit <filename>"""
    if not filename:
        print("Usage: edit <filename>")
        return

    editor = "nano"
    if not shutil.which(editor):
        print(f"{RED}Error: Editor '{editor}' not found. Please install it.{RESET}")
        return

    try:
        abs_filename = os.path.abspath(filename)
        # Basic check to prevent editing critical files directly?
        # critical_abs = [os.path.abspath(p) for p in [USER_CONFIG_FILE, REPO_FILE, MAIN_SCRIPT]]
        # if abs_filename in critical_abs:
        #      print(f"{YELLOW}Warning: Editing critical system file '{filename}'. Be careful!{RESET}")

        if not os.path.exists(abs_filename):
             parent_dir = os.path.dirname(abs_filename)
             if parent_dir and not os.path.exists(parent_dir):
                 os.makedirs(parent_dir)
             touch(abs_filename) # Create empty file if it doesn't exist

        subprocess.run([editor, abs_filename], check=True)

        # Post-Edit Actions
        if abs_filename == os.path.abspath(REPO_FILE):
            print(f"{YELLOW}Repository file edited. Reloading repository...{RESET}")
            load_repository()
        elif abs_filename.endswith("app.conf") and os.path.abspath(APPLICATIONS_DIR) in abs_filename:
             print(f"{YELLOW}Application configuration edited. Reloading applications...{RESET}")
             load_applications()

    except FileNotFoundError: # Should be caught by which, but safety
        print(f"{RED}Error: Editor '{editor}' disappeared unexpectedly?{RESET}")
    except subprocess.CalledProcessError as e:
        print(f"{YELLOW}Editor '{editor}' closed (exit code {e.returncode}).{RESET}")
    except PermissionError:
        print(f"{RED}Error: Permission denied to access or modify '{filename}'.{RESET}")
    except OSError as e:
        print(f"{RED}Error preparing file for editing: {e}{RESET}")
    except Exception as e:
        print(f"{RED}An unexpected error occurred during editing: {e}{RESET}")


def download_file(url, filepath):
    """Helper function to download a file from a URL to a specific path."""
    print(f"Downloading {url} -> {os.path.basename(filepath)} ... ", end="", flush=True)
    try:
        parent_dir = os.path.dirname(filepath)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir)

        response = requests.get(url, stream=True, headers={'User-Agent': 'MyPythonOS Downloader/1.2'}, timeout=30)
        response.raise_for_status()

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
        if os.path.exists(filepath):
             try: os.remove(filepath)
             except OSError: pass
        return False
    except PermissionError:
         print(f"{RED}Failed (Permission Denied writing to '{filepath}'){RESET}")
         return False
    except OSError as e:
        print(f"{RED}Failed (File System Error: {e}){RESET}")
        return False
    except Exception as e:
        print(f"{RED}Failed (Unexpected Error: {e}){RESET}")
        return False


def download(url, destination=None):
    """Downloads a file from a URL. Saves to CWD or specified location.
       Usage: download <url> [directory_or_filename]"""
    if not url:
        print("Usage: download <url> [directory_or_filename]")
        return

    try:
        parsed_url = urlparse(url)
        if not parsed_url.scheme in ['http', 'https']:
             print(f"{RED}Error: Invalid URL scheme. Use http or https.{RESET}")
             return

        filename = os.path.basename(parsed_url.path)
        if not filename:
             timestamp = time.strftime("%Y%m%d-%H%M%S")
             filename = f"download_{timestamp}"
             print(f"{YELLOW}Could not determine filename from URL. Using default: '{filename}'.{RESET}")

        filepath = ""
        if destination:
            if os.path.isdir(destination):
                filepath = os.path.join(destination, filename)
            else:
                 filepath = destination
                 dest_dir = os.path.dirname(filepath)
                 if dest_dir and not os.path.exists(dest_dir):
                     try:
                         print(f"Creating destination directory: {dest_dir}")
                         os.makedirs(dest_dir)
                     except OSError as e:
                         print(f"{RED}Error creating destination directory '{dest_dir}': {e}{RESET}")
                         return
        else:
            filepath = filename

        if os.path.abspath(filepath) in [os.path.abspath(p) for p in [USER_CONFIG_FILE, REPO_FILE, MAIN_SCRIPT]]:
            print(f"{RED}Error: Cannot overwrite critical system file '{os.path.basename(filepath)}' using download.{RESET}")
            return

        download_file(url, filepath)

    except Exception as e:
        print(f"{RED}An unexpected error occurred during download setup: {e}{RESET}")


def javac(filename):
    """Compiles a Java file using javac.
    Usage: javac <filename.java>"""
    if not filename or not filename.endswith(".java"):
        print("Usage: javac <filename.java>")
        return
    try:
        if not os.path.isfile(filename):
             print(f"{RED}Error: Java source file not found: {filename}{RESET}")
             return

        print(f"Compiling {filename}...")
        compiler = "javac"
        if not shutil.which(compiler):
            print(f"{RED}Error: '{compiler}' command not found (JDK required in PATH).{RESET}")
            return

        result = subprocess.run([compiler, filename], check=False, capture_output=True, text=True, encoding='utf-8')

        if result.returncode == 0:
            print(f"{GREEN}Successfully compiled: {filename}{RESET}")
            if result.stderr: print(f"{YELLOW}Compiler Warnings:\n{result.stderr.strip()}{RESET}")
            if result.stdout: print(f"{YELLOW}Compiler Output:\n{result.stdout.strip()}{RESET}")
        else:
            print(f"{RED}Error: Compilation failed for {filename}.{RESET}")
            if result.stderr: print(f"Stderr:\n{result.stderr.strip()}")
            if result.stdout: print(f"Stdout:\n{result.stdout.strip()}")

    except Exception as e:
        print(f"{RED}An unexpected error occurred during Java compilation: {e}{RESET}")

def run(filename):
    """Runs a code file (Python, Java Class, Lua, or JavaScript).
    Usage: run <filename>"""
    if not filename:
        print("Usage: run <filename>")
        return

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

        if ext == ".py":
            if shutil.which("python3"): interpreter = "python3"
            elif shutil.which("python"): interpreter = "python"
            else: raise FileNotFoundError("No Python interpreter ('python3' or 'python') found")
            cmd = [interpreter, file_to_run]
        elif ext == ".class":
            if not shutil.which("java"): raise FileNotFoundError("'java' command not found (JRE/JDK needed)")
            class_name = os.path.splitext(os.path.basename(filename))[0]
            class_dir = os.path.dirname(os.path.abspath(filename))
            cmd = ["java", "-cp", class_dir, class_name]
            print(f"Attempting to run Java class: {class_name} (classpath={class_dir})")
        elif ext == ".lua":
             if not shutil.which("lua"): raise FileNotFoundError("'lua' command not found")
             cmd = ["lua", file_to_run]
        elif ext == ".js":
            if not shutil.which("node"): raise FileNotFoundError("'node' command not found (Node.js needed)")
            cmd = ["node", file_to_run]
        elif ext in [".sh", ".bash"]:
             if shutil.which("bash"): interpreter = "bash"
             elif shutil.which("sh"): interpreter = "sh"
             else: raise FileNotFoundError("No Shell interpreter ('bash' or 'sh') found")
             if not os.access(file_to_run, os.X_OK) and os.name != 'nt':
                 print(f"{YELLOW}Warning: Shell script '{filename}' is not executable. Attempting to run anyway...{RESET}")
             cmd = [interpreter, file_to_run]
        else:
            print(f"{RED}Error: Unsupported file type for 'run': {filename}{RESET}")
            print("Supported types: .py, .class, .lua, .js, .sh, .bash")
            return

        print(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)

    except FileNotFoundError as e:
        print(f"{RED}Error: {e}{RESET}")
        print("Please ensure the required interpreter is installed and in your system's PATH.")
    except PermissionError:
         print(f"{RED}Error: Permission denied to execute '{filename}' or its interpreter.{RESET}")
    except subprocess.CalledProcessError as e:
        print(f"{RED}Error: Execution failed for '{filename}' (exit code {e.returncode}).{RESET}")
    except Exception as e:
        print(f"{RED}An unexpected error occurred while trying to run '{filename}': {e}{RESET}")


def cowsay(text_args):
    """Displays text using an embedded cowsay. Text wraps automatically.
       Usage: cowsay <text>"""
    if not text_args: text = "Moo?"
    else: text = " ".join(text_args)

    max_line_len = 38
    lines = []
    current_line = ""
    for word in text.split():
        if not current_line: current_line = word
        elif len(current_line) + len(word) + 1 <= max_line_len: current_line += " " + word
        else:
            lines.append(current_line)
            current_line = word
    if current_line: lines.append(current_line)
    if not lines: lines.append("")

    box_width = max(len(line) for line in lines)
    message = ""
    if len(lines) == 1:
        message = f"< {lines[0]} >"
        top_border = f" {'_' * (box_width + 2)} "
        bottom_border = f" {'-' * (box_width + 2)} "
    else:
        top_border = f" /{'-' * (box_width + 2)}\\"
        message += f"| {lines[0]:<{box_width}} |\n"
        for i in range(1, len(lines) - 1): message += f"| {lines[i]:<{box_width}} |\n"
        message += f"| {lines[-1]:<{box_width}} |"
        bottom_border = f" \\{'-' * (box_width + 2)}/"

    cow = f"""
   {top_border}
    {message}
   {bottom_border}
            \\   ^__^
             \\  (oo)\\_______
                (__)\\       )\\/\\
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
            if ":" in line:
                key, value = line.split(":", 1)
                conf_data[key.strip().lower()] = value.strip()
            else:
                 print(f"{YELLOW}Warning: Malformed line {line_num} in app config content (missing ':'). Ignored: '{line}'{RESET}")
    except Exception as e:
        print(f"{RED}Error parsing app.conf content: {e}{RESET}")
        return None
    return conf_data


def install(identifier):
    """Installs an app using an installer config URL or a repo name.
       The installer config specifies URLs for the final app.conf and scripts.
       Usage: install <url_or_name>"""
    if not identifier:
        print("Usage: install <url_or_name>")
        print("Use 'repo list' to see available names.")
        return

    installer_config_url = ""
    # Resolve identifier to URL
    if identifier in APP_REPOSITORY:
        installer_config_url = APP_REPOSITORY[identifier]
        print(f"Found '{identifier}' in repository. Using installer config URL: {installer_config_url}")
    else:
        installer_config_url = identifier
        parsed_url = urlparse(installer_config_url)
        if not parsed_url.scheme in ['http', 'https'] or not parsed_url.netloc:
             print(f"{RED}Error: Invalid URL or unknown app name: {identifier}{RESET}")
             return
        print(f"Using direct installer config URL: {installer_config_url}")

    # --- Step 1: Fetch and Parse the *Installer* Config ---
    try:
        print(f"Fetching installer config from: {installer_config_url} ... ", end="", flush=True)
        installer_resp = requests.get(installer_config_url, headers={'User-Agent': 'MyPythonOS Installer/1.2'}, timeout=20)
        installer_resp.raise_for_status()
        print(f"{GREEN}Success{RESET}")

        installer_data = {}
        optional_urls = []
        # Parse the installer config (folder-name, conf-url, script-url, optional-url)
        for line_num, line in enumerate(installer_resp.text.splitlines(), 1):
            line = line.strip()
            if not line or line.startswith('#'): continue
            if ":" in line:
                key, value = line.split(":", 1)
                key, value = key.strip().lower(), value.strip()
                if not value:
                     print(f"{YELLOW}Warning: Empty value for key '{key}' at line {line_num} in installer config. Skipping.{RESET}")
                     continue

                if key == "optional-url":
                    optional_urls.append(value)
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
            print(f"{RED}Error: Invalid installer configuration from {installer_config_url}.{RESET}")
            missing = [k for k in ['folder-name', 'conf-url', 'script-url'] if not installer_data.get(k)]
            print(f"Missing required fields in installer config: {', '.join(missing)}")
            return

    except requests.exceptions.RequestException as e:
        print(f"{RED}\nError: Failed to fetch installer configuration: {e}{RESET}")
        return
    except Exception as e:
        print(f"{RED}\nAn unexpected error occurred while processing installer config: {e}{RESET}")
        return


    # --- Step 2: Fetch and Parse the *Final app.conf* Content (for validation and info) ---
    local_conf_content = None
    app_name = None
    command_name = None
    version = "N/A"
    main_script_filename = None
    try:
        print(f"Fetching final app config from: {conf_url} ... ", end="", flush=True)
        conf_resp = requests.get(conf_url, headers={'User-Agent': 'MyPythonOS Installer/1.2'}, timeout=20)
        conf_resp.raise_for_status()
        local_conf_content = conf_resp.text # Store the content to write later
        print(f"{GREEN}Success{RESET}")

        # Parse the content to get app details for validation/conflict check
        app_conf_data = parse_app_conf_content(local_conf_content)
        if not app_conf_data:
             print(f"{RED}Error: Could not parse the content from conf-url: {conf_url}{RESET}")
             return

        app_name = app_conf_data.get("name")
        command_name = app_conf_data.get("command", app_name) # Default command to name
        version = app_conf_data.get("version", "N/A")
        main_script_filename = app_conf_data.get("file")

        if not app_name or not command_name or not main_script_filename:
             print(f"{RED}Error: The final app config fetched from {conf_url} is invalid.{RESET}")
             missing = []
             if not app_name: missing.append("'name'")
             if not command_name: missing.append("'command'")
             if not main_script_filename: missing.append("'file'")
             print(f"Missing required fields in final app config: {', '.join(missing)} (command defaults to name)")
             return

        # Verify script filename consistency
        script_url_filename = os.path.basename(urlparse(script_url).path)
        if script_url_filename != main_script_filename:
             print(f"{YELLOW}Warning: Script filename from script-url ('{script_url_filename}')")
             print(f"         does not match filename 'file:' in app.conf ('{main_script_filename}').")
             print(f"         Saving script as '{main_script_filename}' based on app.conf.{RESET}")


    except requests.exceptions.RequestException as e:
        print(f"{RED}\nError: Failed to fetch final app configuration from {conf_url}: {e}{RESET}")
        return
    except Exception as e:
        print(f"{RED}\nAn unexpected error occurred while processing final app config: {e}{RESET}")
        return

    # --- Step 3: Conflict Check and Directory Preparation ---
    if command_name in globals() and callable(globals()[command_name]):
        print(f"{RED}Error: Proposed command '{command_name}' (from app '{app_name}') conflicts with a built-in OS command. Installation aborted.{RESET}")
        return
    if command_name in INSTALLED_APPS:
        existing_app = INSTALLED_APPS[command_name]['name']
        print(f"{RED}Error: Command '{command_name}' is already used by application '{existing_app}'. Installation aborted.{RESET}")
        return

    app_dir = os.path.join(APPLICATIONS_DIR, folder_name)
    if os.path.exists(app_dir):
        overwrite = input(f"{YELLOW}Application directory '{app_dir}' already exists. Overwrite? (y/N): {RESET}").lower()
        if overwrite == 'y':
            print(f"Removing existing directory: {app_dir}")
            try: shutil.rmtree(app_dir)
            except OSError as e:
                print(f"{RED}Error removing existing directory: {e}. Installation aborted.{RESET}")
                return
        else:
            print("Installation aborted by user.")
            return
    try:
        os.makedirs(app_dir)
        print(f"Created application directory: {app_dir}")
    except OSError as e:
        print(f"{RED}Error creating application directory '{app_dir}': {e}. Installation aborted.{RESET}")
        return

    # --- Step 4: Download and Save Files ---
    success = True
    files_to_cleanup = []

    # Save the final app.conf
    conf_filepath = os.path.join(app_dir, "app.conf")
    try:
        with open(conf_filepath, "w", encoding='utf-8') as f: # Specify encoding
            f.write(local_conf_content)
        print(f"Saved configuration file: {os.path.basename(conf_filepath)}")
        files_to_cleanup.append(conf_filepath)
    except OSError as e:
        print(f"{RED}Error saving configuration file: {e}. Installation aborted.{RESET}")
        success = False

    # Download the main script
    if success:
        # Use the filename specified in the app.conf ('file:')
        script_filepath = os.path.join(app_dir, main_script_filename)
        if download_file(script_url, script_filepath):
            files_to_cleanup.append(script_filepath)
        else:
            print(f"{RED}Failed to download main script file from {script_url}. Installation aborted.{RESET}")
            success = False

    # Download optional files
    if success:
        for opt_url in optional_urls:
            opt_filename = os.path.basename(urlparse(opt_url).path)
            if not opt_filename:
                print(f"{YELLOW}Warning: Could not determine filename for optional URL: {opt_url}. Skipping.{RESET}")
                continue
            opt_filepath = os.path.join(app_dir, opt_filename)
            if download_file(opt_url, opt_filepath):
                files_to_cleanup.append(opt_filepath)
            else:
                print(f"{YELLOW}Warning: Failed to download OPTIONAL file: {opt_filename}. Continuing installation.{RESET}")


    # --- Step 5: Cleanup or Finalize ---
    if not success:
        print(f"{RED}Installation failed. Cleaning up...{RESET}")
        try:
            shutil.rmtree(app_dir)
            print(f"Removed incomplete application directory: {app_dir}")
        except OSError as e:
            print(f"{RED}Error during cleanup: {e}{RESET}")
        return

    # Finalize: Make script executable (if needed) and reload apps
    print(f"{GREEN}Successfully installed application '{app_name}' (command: {command_name} v{version}).{RESET}")
    main_script_path = os.path.join(app_dir, main_script_filename)
    if os.path.exists(main_script_path) and os.name != 'nt':
         try:
             # Add execute permissions for user, group, others (ugo+x)
             current_mode = os.stat(main_script_path).st_mode
             os.chmod(main_script_path, current_mode | 0o111)
             print(f"Made '{main_script_filename}' executable.")
         except OSError as e:
             print(f"{YELLOW}Warning: Could not make script '{main_script_filename}' executable: {e}{RESET}")

    load_applications() # Reload applications


def setup_app(app_dir):
    """Reads app.conf and registers an application command."""
    conf_file = os.path.join(app_dir, "app.conf")

    if not os.path.isfile(conf_file): return # Not an app dir

    try:
        conf_data = {}
        with open(conf_file, "r", encoding='utf-8') as f: # Specify encoding
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'): continue
                if ":" in line:
                    key, value = line.split(":", 1)
                    conf_data[key.strip().lower()] = value.strip()

        name = conf_data.get("name")
        command = conf_data.get("command")
        version = conf_data.get("version", "N/A")
        file_to_run = conf_data.get("file")

        if not name or not command or not file_to_run:
            print(f"{YELLOW}Warning: Invalid app.conf in '{os.path.basename(app_dir)}'. Missing 'name', 'command', or 'file'. Skipping.{RESET}")
            return

        # Use absolute paths for reliability
        abs_app_dir = os.path.abspath(app_dir)
        script_path = os.path.join(abs_app_dir, file_to_run)

        if not os.path.exists(script_path):
            print(f"{YELLOW}Warning: Specified script file '{file_to_run}' not found in '{os.path.basename(app_dir)}' for app '{name}'. Skipping.{RESET}")
            return

        if command in globals() and callable(globals()[command]):
            print(f"{YELLOW}Warning: Command '{command}' (from app '{name}') conflicts with a built-in command. Skipping app.{RESET}")
            return
        if command in INSTALLED_APPS:
            print(f"{YELLOW}Warning: Command '{command}' conflict between '{name}' and '{INSTALLED_APPS[command]['name']}'. Keeping first loaded. Skipping '{name}'.{RESET}")
            return

        INSTALLED_APPS[command] = {
            "name": name,
            "script": script_path, # Store absolute path
            "version": version,
            "app_dir": abs_app_dir # Store absolute path
        }

    except OSError as e:
         print(f"{RED}Error reading configuration for app in '{os.path.basename(app_dir)}': {e}{RESET}")
    except Exception as e:
        print(f"{RED}Error setting up app from {os.path.basename(app_dir)}: {e}{RESET}")

def load_applications():
    """Loads applications from the applications directory."""
    global INSTALLED_APPS
    INSTALLED_APPS.clear()

    if not os.path.exists(APPLICATIONS_DIR):
        try:
            os.makedirs(APPLICATIONS_DIR)
            print(f"Created 'applications' directory: {APPLICATIONS_DIR}")
        except OSError as e:
            print(f"{RED}Error: Could not create 'applications' directory: {e}{RESET}")
            return

    app_count = 0
    try:
        for item in os.listdir(APPLICATIONS_DIR):
            item_path = os.path.join(APPLICATIONS_DIR, item)
            if os.path.isdir(item_path):
                original_app_count = len(INSTALLED_APPS)
                setup_app(item_path)
                if len(INSTALLED_APPS) > original_app_count:
                    app_count += 1
    except OSError as e:
         print(f"{RED}Error listing applications directory '{APPLICATIONS_DIR}': {e}{RESET}")

    if app_count > 0:
        print(f"{GREEN}Loaded {app_count} applications.{RESET}")


def app(command, args):
    """Runs an installed application command with arguments."""
    if command not in INSTALLED_APPS:
        print(f"{RED}Error: Application command '{command}' not found.{RESET}")
        return

    app_info = INSTALLED_APPS[command]
    script_file = app_info["script"] # Absolute path
    app_dir = app_info["app_dir"]   # Absolute path

    interpreter = None
    cmd = []
    ext = os.path.splitext(script_file)[1].lower()

    original_cwd = os.getcwd() # Store CWD before changing
    try:
         os.chdir(app_dir) # Change CWD to the app's directory
         print(f"Running '{app_info['name']}' (v{app_info['version']})...")

         if ext == ".py":
             if shutil.which("python3"): interpreter = "python3"
             elif shutil.which("python"): interpreter = "python"
             else: raise FileNotFoundError("No Python interpreter found")
             cmd = [interpreter, script_file] + args
         elif ext == ".js":
             if not shutil.which("node"): raise FileNotFoundError("Node.js interpreter 'node' not found")
             cmd = ["node", script_file] + args
         elif ext == ".lua":
             if not shutil.which("lua"): raise FileNotFoundError("Lua interpreter 'lua' not found")
             cmd = ["lua", script_file] + args
         elif ext in [".sh", ".bash"]:
             if shutil.which("bash"): interpreter = "bash"
             elif shutil.which("sh"): interpreter = "sh"
             else: raise FileNotFoundError("No Shell interpreter ('bash' or 'sh') found")
             if not os.access(script_file, os.X_OK) and os.name != 'nt':
                 print(f"{YELLOW}Warning: App script '{os.path.basename(script_file)}' is not executable. Trying anyway...{RESET}")
             cmd = [interpreter, script_file] + args
         else:
             if not os.access(script_file, os.X_OK):
                 if os.name != 'nt': # Attempt chmod only on Unix-like
                     print(f"{YELLOW}App file '{os.path.basename(script_file)}' is not executable. Attempting chmod...{RESET}")
                     try: os.chmod(script_file, os.stat(script_file).st_mode | 0o111)
                     except OSError as chmod_e:
                         print(f"{RED}Failed to make executable: {chmod_e}{RESET}")
                         raise PermissionError("Application file is not executable") # Raise error if chmod fails
                 else: # On Windows, non-executable might still run via association
                      print(f"{YELLOW}Warning: App file '{os.path.basename(script_file)}' may not be directly executable on Windows.{RESET}")

             print(f"{YELLOW}Attempting direct execution of {os.path.basename(script_file)}...{RESET}")
             cmd = [script_file] + args

         # Execute
         subprocess.run(cmd, check=True)

    except FileNotFoundError as e:
        print(f"{RED}Error running app '{app_info['name']}': {e}{RESET}")
    except PermissionError as e:
        print(f"{RED}Error running app '{app_info['name']}': Permission denied - {e}{RESET}")
    except OSError as e: # Handle other OS errors like "Exec format error"
        print(f"{RED}Error executing application '{app_info['name']}': {e}{RESET}")
    except subprocess.CalledProcessError as e:
        print(f"{YELLOW}Application '{app_info['name']}' exited with non-zero status ({e.returncode}).{RESET}")
    except Exception as e:
        print(f"{RED}An unexpected error occurred while running app '{command}': {e}{RESET}")
    finally:
         # ALWAYS change back to original CWD
         try:
             os.chdir(original_cwd)
         except OSError as cd_err: # Handle if original CWD somehow got deleted
             print(f"{RED}Error: Could not change back to original directory '{original_cwd}': {cd_err}{RESET}")
             try:
                 os.chdir(ROOT_PATH) # Go to root as fallback
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

    if subcommand == "list":
        if not APP_REPOSITORY:
            print("Repository is empty or not loaded.")
            print(f"Try 'repo update' or manually edit '{os.path.basename(REPO_FILE)}'.")
            return
        print(f"--- Application Repository ('{os.path.basename(REPO_FILE)}') ---")
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
        if download_file(url_to_update, REPO_FILE):
            print(f"{GREEN}Repository file updated successfully. Reloading...{RESET}")
            load_repository()
        else:
            print(f"{RED}Failed to update repository file from the URL.{RESET}")

    elif subcommand == "add":
        if len(args) != 3: print("Usage: repo add <name> <url>"); return
        name, url = args[1], args[2]
        if not name or ":" in name or name.startswith('#'): print(f"{RED}Error: Invalid name '{name}'.{RESET}"); return
        parsed_url = urlparse(url);
        if not parsed_url.scheme in ['http', 'https'] or not parsed_url.netloc: print(f"{RED}Error: Invalid URL '{url}'.{RESET}"); return

        entry_exists = name in APP_REPOSITORY
        if entry_exists:
             print(f"{YELLOW}Warning: Name '{name}' already exists: {APP_REPOSITORY[name]}{RESET}")
             overwrite = input(f"Overwrite with new URL '{url}'? (y/N): ").lower()
             if overwrite != 'y': print("Add operation cancelled."); return

        APP_REPOSITORY[name] = url
        try:
            temp_repo_file = REPO_FILE + ".tmp"
            with open(temp_repo_file, "w", encoding='utf-8') as f:
                for n, u in sorted(APP_REPOSITORY.items()): f.write(f"{n}\n{u}\n")
            shutil.move(temp_repo_file, REPO_FILE)
            print(f"{GREEN}{'Updated' if entry_exists else 'Added'} '{name}' in repository.{RESET}")
        except (OSError, Exception) as e:
            print(f"{RED}Error writing updated repository file: {e}{RESET}")
            print(f"{YELLOW}Reloading repository from original file...{RESET}")
            load_repository() # Revert memory change

    elif subcommand == "remove":
        if len(args) != 2: print("Usage: repo remove <name>"); return
        name = args[1]
        if name not in APP_REPOSITORY: print(f"{RED}Error: Name '{name}' not found.{RESET}"); return

        print(f"Removing '{name}' ({APP_REPOSITORY[name]}) ...")
        del APP_REPOSITORY[name]
        try:
            temp_repo_file = REPO_FILE + ".tmp"
            with open(temp_repo_file, "w", encoding='utf-8') as f:
                if APP_REPOSITORY:
                     for n, u in sorted(APP_REPOSITORY.items()): f.write(f"{n}\n{u}\n")
            shutil.move(temp_repo_file, REPO_FILE)
            print(f"{GREEN}Removed '{name}' from repository.{RESET}")
        except (OSError, Exception) as e:
            print(f"{RED}Error writing updated repository file: {e}{RESET}")
            print(f"{YELLOW}Reloading repository from original file...{RESET}")
            load_repository() # Revert memory change

    else:
        print(f"{RED}Error: Unknown repo subcommand '{subcommand}'.{RESET}")


# --- Panic Command ---

def delpanic():
    """Deletes most files/dirs in root, except critical ones. Requires confirmation."""
    preserve_relative = [
        os.path.basename(MAIN_SCRIPT),
        os.path.basename(USER_CONFIG_FILE),
        os.path.basename(REPO_FILE),
        os.path.basename(APPLICATIONS_DIR)
    ]
    preserve_absolute = [os.path.abspath(os.path.join(ROOT_PATH, p)) for p in preserve_relative]

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
    print(f"{RED}This action is EXTREMELY DESTRUCTIVE. Data loss is likely permanent.{RESET}")
    print(f"{YELLOW}To confirm, please type the following {num_confirm} sentences exactly:{RESET}")
    for i, sentence in enumerate(chosen_sentences): print(f"  {i + 1}: {sentence}")

    for i in range(num_confirm):
        try:
            user_input = input(f"Sentence {i + 1}/{num_confirm}: ").strip()
            if user_input != chosen_sentences[i]: print(f"{RED}Confirmation failed. Aborting DELPANIC.{RESET}"); return
        except (EOFError, KeyboardInterrupt): print(f"\n{RED}Confirmation aborted. Aborting DELPANIC.{RESET}"); return

    print(f"{GREEN}Confirmation successful. Proceeding with DELPANIC in 3 seconds... (Ctrl+C to abort){RESET}")
    try: time.sleep(3)
    except KeyboardInterrupt: print(f"\n{RED}DELPANIC aborted by user.{RESET}"); return

    print(f"{RED}--- EXECUTING DELPANIC ---{RESET}")
    deleted_count, error_count = 0, 0
    try:
        for item_name in os.listdir(ROOT_PATH):
            item_path_abs = os.path.abspath(os.path.join(ROOT_PATH, item_name))
            if item_path_abs in preserve_absolute: print(f"Skipping preserved: {item_name}"); continue
            try:
                if os.path.isfile(item_path_abs):
                    print(f"Deleting file: {item_name} ... ", end="", flush=True)
                    # Optional: Secure overwrite (slow)
                    # try:
                    #     with open(item_path_abs, "wb") as f: f.write(b"\0" * os.path.getsize(item_path_abs))
                    # except OSError as oe: print(f"[Overwrite Error: {oe}] ", end="")
                    os.remove(item_path_abs)
                    print(f"{GREEN}OK{RESET}"); deleted_count += 1
                elif os.path.isdir(item_path_abs):
                    print(f"Deleting directory: {item_name} ... ", end="", flush=True)
                    shutil.rmtree(item_path_abs)
                    print(f"{GREEN}OK{RESET}"); deleted_count += 1
                else: print(f"Skipping non-file/dir: {item_name}")
            except Exception as e: print(f"{RED}ERROR deleting '{item_name}': {e}{RESET}"); error_count += 1
    except OSError as e: print(f"{RED}Fatal Error listing directory {ROOT_PATH}: {e}{RESET}"); error_count +=1

    print(f"{GREEN}--- DELPANIC Complete ---{RESET}")
    print(f"Items deleted: {deleted_count}")
    if error_count > 0: print(f"{RED}Errors occurred: {error_count}{RESET}")


# --- Main Loop ---

def get_prompt(username, hostname):
    """Generates the custom prompt showing user@host:path $."""
    try:
        try: cwd = os.getcwd()
        except FileNotFoundError:
             print(f"{YELLOW}Warning: Current working directory lost. Returning to root.{RESET}")
             os.chdir(ROOT_PATH); cwd = ROOT_PATH

        display_path = ""
        root_path_abs = os.path.abspath(ROOT_PATH)
        cwd_abs = os.path.abspath(cwd)

        if cwd_abs == root_path_abs: display_path = "~"
        elif os.path.commonpath([root_path_abs, cwd_abs]) == root_path_abs:
             relative_path = os.path.relpath(cwd_abs, root_path_abs)
             # Replace backslashes for Windows display consistency
             display_path = f"~/{relative_path.replace(os.sep, '/')}"
        else: display_path = cwd_abs # Show full path if outside root

        return f"{GREEN}{username}@{hostname}{RESET}:{BLUE}{display_path}{RESET} $ "
    except OSError as e:
         print(f"\n{RED}Error getting prompt information: {e}. Using basic prompt.{RESET}")
         return f"{username}@{hostname}:{RED}???{RESET} $ "


def main():
    """Main loop of the simulated terminal."""
    global ROOT_PATH

    clear()
    print(f"Welcome to MyPythonOS!")
    print(f"Root directory: {ROOT_PATH}")
    print(f"Type 'help' for commands, 'exit' to quit.")
    print("-" * 30)

    # --- Initial Setup ---
    # Ensure critical dirs exist
    if not os.path.exists(APPLICATIONS_DIR):
         try: os.makedirs(APPLICATIONS_DIR)
         except OSError: print(f"{RED}Warning: Could not pre-create applications directory.{RESET}")

    username, hostname = load_user_config()
    if not username or not hostname:
        print("Performing first-time user setup...")
        username, hostname = create_user_config()
        print("-" * 30)

    # --- Repository Setup ---
    if not os.path.exists(REPO_FILE):
        print(f"Repository file '{os.path.basename(REPO_FILE)}' not found.")
        print(f"Attempting to download initial repository...")
        if download_file(DEFAULT_REPO_URL, REPO_FILE):
            print(f"{GREEN}Successfully downloaded initial repository.{RESET}")
        else:
            print(f"{YELLOW}Warning: Failed to download initial repository.{RESET}")
            print(f"You can try 'repo update' later or create '{os.path.basename(REPO_FILE)}' manually.")
        print("-" * 30)

    load_repository()
    load_applications()
    print("-" * 30)

    try: os.chdir(ROOT_PATH)
    except OSError as e:
        print(f"{RED}Fatal Error: Could not change to root directory '{ROOT_PATH}': {e}{RESET}")
        return

    # --- Command Loop ---
    while True:
        try:
            prompt = get_prompt(username, hostname)
            command_line = input(prompt).strip()

            if not command_line: continue

            parts = command_line.split()
            cmd = parts[0]
            args = parts[1:]

            # --- Command Dispatching ---
            if cmd == "exit": print("Exiting MyPythonOS..."); break
            elif cmd == "help": help()
            elif cmd == "clear": clear()
            elif cmd == "neofetch": neofetch()
            # Filesystem
            elif cmd == "ls": ls(args)
            elif cmd == "delf": delf(args[0] if args else None)
            elif cmd == "deld": deld(args[0] if args else None)
            elif cmd == "cd": cd(args[0] if args else None)
            elif cmd == "pwd": pwd()
            elif cmd == "mkdir": mkdir(args[0] if args else None)
            elif cmd == "touch": touch(args[0] if args else None)
            elif cmd == "move": move(args[0] if len(args)>0 else None, args[1] if len(args)>1 else None)
            # Editing & Execution
            elif cmd == "edit": edit(args[0] if args else None)
            elif cmd == "javac": javac(args[0] if args else None)
            elif cmd == "run": run(args[0] if args else None)
            # Network & Apps
            elif cmd == "download": download(args[0] if len(args)>0 else None, args[1] if len(args)>1 else None)
            elif cmd == "install": install(args[0] if args else None)
            elif cmd == "repo": repo(args)
            # Fun & Danger
            elif cmd == "cowsay": cowsay(args)
            elif cmd == "delpanic": delpanic()
            # Check Installed Apps
            elif cmd in INSTALLED_APPS: app(cmd, args)
            # Unknown Command
            else: print(f"{RED}Command not found: {cmd}{RESET}")

        except KeyboardInterrupt: print("\n^C") # Mimic shell interrupt
        except EOFError: print("\nexit"); break # Mimic shell EOF (Ctrl+D)
        except Exception as e: # Catch unexpected errors
             print(f"\n{RED}--- UNEXPECTED OS ERROR ---{RESET}")
             print(f"{RED}An error occurred processing the command:{RESET}")
             traceback.print_exc() # Print full traceback for debugging
             print(f"{YELLOW}Attempting to continue...{RESET}")


if __name__ == "__main__":
    main()
    print(f"{ORANGE}MyPythonOS session ended.{RESET}")
