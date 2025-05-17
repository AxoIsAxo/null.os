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

# Attempt to import readline for command history and better input
try:
    import readline
    # GNU Readline is available
except ImportError:
    try:
        import pyreadline3 as readline # For Windows
        # pyreadline3 might require specific setup for some features,
        # but basic history usually works by just importing.
        # This print statement might appear before colors are fully set up if it's very early
        # print(f"\033[93mUsing pyreadline3 for history/input on Windows.\033[0m") # Manual color for early print
    except ImportError:
        readline = None # No readline library found
        # This print statement might appear before colors are fully set up
        # print(f"\033[93mWarning: readline library not found. Command history and advanced line editing will not be available.\033[0m")
        # print(f"\033[93m  On Linux/macOS, ensure 'readline' is installed.\033[0m")
        # print(f"\033[93m  On Windows, try: pip install pyreadline3\033[0m")


# ANSI escape codes for colors
RED = '\033[91m'
ORANGE = '\033[38;5;208m'  # A good orange color
YELLOW = '\033[93m'
GREEN = '\033[92m'
BLUE = '\033[94m'
PURPLE = '\033[95m'
RESET = '\033[0m'

# --- Constants ---
ROOT_DIR_NAME = "root"
ROOT_PATH = os.path.abspath("./")
USER_CONFIG_FILE = os.path.join(ROOT_PATH, "user.json")
APPLICATIONS_DIR = os.path.join(ROOT_PATH, "applications")
REPO_FILE = os.path.join(ROOT_PATH, "repo.txt")
DEFAULT_REPO_URL = "https://raw.githubusercontent.com/AxoIsAxo/null.os/refs/heads/main/repo.txt"
HISTORY_FILE = os.path.join(ROOT_PATH, ".mypythos_history") # For command history
HISTORY_MAX_LINES = 1000 # Max lines to keep in history

try:
    MAIN_SCRIPT = os.path.basename(__file__)
except NameError:
    MAIN_SCRIPT = "mypythonos_script.py"


# --- Global State ---
INSTALLED_APPS = {}
APP_REPOSITORY = {}
username = "user"
hostname = "mypythos"

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
    if not _username: _username = "user"
    _hostname = input("Enter hostname: ").strip()
    if not _hostname: _hostname = "mypythos"

    config = {"username": _username, "hostname": _hostname}

    try:
        with open(USER_CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
        print(f"{GREEN}User configuration saved to user.json{RESET}")
        return _username, _hostname
    except OSError as e:
        print(f"{RED}Error: Could not create user.json: {e}{RESET}")
        return "user", "mypythos"


def load_repository():
    """Loads application repository information from repo.txt."""
    global APP_REPOSITORY
    APP_REPOSITORY.clear()

    if not os.path.exists(REPO_FILE):
        return

    try:
        with open(REPO_FILE, "r") as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]

        if not lines:
             return

        if len(lines) % 2 != 0:
            print(f"{YELLOW}Warning: Malformed repository file '{os.path.basename(REPO_FILE)}'. Odd number of lines after comments. Ignoring last line.{RESET}")
            lines = lines[:-1]

        entries_loaded = 0
        for i in range(0, len(lines), 2):
            name = lines[i]
            url = lines[i+1]
            if name and url:
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

{RESET}"""

ANSI_ESCAPE_RE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def calculate_visual_width(text):
    return len(ANSI_ESCAPE_RE.sub('', text))

NEOFETCH_ART_LINES = NEOFETCH_ART.strip('\n').split('\n')
NEOFETCH_ART_MIN_WIDTH = 0
for line in NEOFETCH_ART_LINES:
    NEOFETCH_ART_MIN_WIDTH = max(NEOFETCH_ART_MIN_WIDTH, calculate_visual_width(line))
NEOFETCH_ART_MIN_WIDTH += 2

def neofetch():
    DEFAULT_WIDTH = 80
    try:
        terminal_width = os.get_terminal_size().columns
    except OSError:
        print(f"{YELLOW}Warning: Could not determine terminal size. Assuming width {DEFAULT_WIDTH}.{RESET}")
        terminal_width = DEFAULT_WIDTH

    if terminal_width >= NEOFETCH_ART_MIN_WIDTH:
        print(NEOFETCH_ART)
    else:
        title = "--- MyPythonOS Info ---"
        clean_title_len = calculate_visual_width(title)
        if terminal_width >= clean_title_len:
            padding = (terminal_width - clean_title_len) // 2
            print(" " * padding + title)
        else:
            print(title)
        print("-" * terminal_width)

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
        num_files, num_dirs = "N/A", "N/A"

    display_path = ""
    root_path_abs = os.path.abspath(ROOT_PATH)
    cwd_abs = os.path.abspath(cwd)
    if cwd_abs == root_path_abs: display_path = "~"
    elif cwd_abs.startswith(root_path_abs + os.sep):
         relative_path = os.path.relpath(cwd_abs, root_path_abs)
         display_path = f"~/{relative_path.replace(os.sep, '/')}"
    else: display_path = cwd_abs

    print(f"""
OS: {os_name}
Kernel: {kernel}
Architecture: {architecture}
Python: {python_version}
Files in CWD: {num_files}
Dirs in CWD: {num_dirs}
CWD: {display_path}
""")

# --- Core File System Commands ---

def ls(args=None):
    if args is None: args = []
    try:
        detailed = False
        if args and args[0] == "-l":
            detailed = True; args = args[1:]
        target_dir = os.getcwd()
        items = sorted(os.listdir(target_dir))
        for item in items:
            try:
                 item_path = os.path.join(target_dir, item)
                 if detailed:
                     stat_info = os.stat(item_path); size = stat_info.st_size
                     if os.path.isdir(item_path): print(f"{BLUE}d {size:>10} {item}/{RESET}")
                     elif os.path.isfile(item_path): print(f"- {size:>10} {item}{RESET}")
                     else: print(f"? {size:>10} {item}{RESET}")
                 else:
                     if os.path.isdir(item_path): print(f"{BLUE}{item}{RESET}/")
                     elif os.path.isfile(item_path) and ((os.access(item_path, os.X_OK) and os.name != 'nt') or \
                                                        (item.split('.')[-1].lower() in ['exe', 'bat', 'com', 'cmd'] and os.name == 'nt')):
                          print(f"{GREEN}{item}{RESET}*")
                     elif os.path.isfile(item_path): print(item)
                     else: print(f"{ORANGE}{item}{RESET}")
            except OSError: print(f"{RED}Error reading: {item}{RESET}")
    except FileNotFoundError: print(f"{RED}Error: Directory not found: {target_dir}{RESET}")
    except OSError as e: print(f"{RED}Error listing directory: {e}{RESET}")

def delf(args):
    if not args: print("Usage: delf <filename>"); return
    filename = args[0]
    try:
        target_path_abs = os.path.abspath(filename)
        critical_files_abs = [os.path.abspath(p) for p in [USER_CONFIG_FILE, REPO_FILE, MAIN_SCRIPT]]
        if target_path_abs in critical_files_abs:
            print(f"{RED}Error: Cannot delete critical system file '{os.path.basename(filename)}' using delf.{RESET}"); return
        os.remove(filename); print(f"Deleted file: {filename}")
    except FileNotFoundError: print(f"{RED}Error: File not found: {filename}{RESET}")
    except IsADirectoryError: print(f"{RED}Error: '{filename}' is a directory. Use 'deld' to delete directories.{RESET}")
    except PermissionError: print(f"{RED}Error: Permission denied to delete '{filename}'.{RESET}")
    except OSError as e: print(f"{RED}Error deleting file '{filename}': {e}{RESET}")

def deld(args):
    if not args: print("Usage: deld <directory>"); return
    dirname = args[0]
    try:
        target_path = os.path.abspath(dirname)
        root_path_abs = os.path.abspath(ROOT_PATH)
        current_path_abs = os.path.abspath(os.getcwd())
        apps_dir_abs = os.path.abspath(APPLICATIONS_DIR)
        if target_path == root_path_abs: print(f"{RED}Error: Cannot delete the root directory ('{ROOT_DIR_NAME}').{RESET}"); return
        if target_path == current_path_abs: print(f"{RED}Error: Cannot delete the current working directory. 'cd' out first.{RESET}"); return
        if target_path == apps_dir_abs:
             print(f"{RED}Error: Cannot delete the main applications directory ('{os.path.basename(APPLICATIONS_DIR)}') using deld.{RESET}")
             print(f"{YELLOW}Delete individual app directories inside it or use 'uninstall' command.{RESET}"); return
        shutil.rmtree(target_path); print(f"Deleted directory: {dirname}")
    except FileNotFoundError: print(f"{RED}Error: Directory not found: {dirname}{RESET}")
    except NotADirectoryError: print(f"{RED}Error: '{dirname}' is not a directory.{RESET}")
    except PermissionError: print(f"{RED}Error: Permission denied to delete directory '{dirname}'.{RESET}")
    except OSError as e: print(f"{RED}Error deleting directory '{dirname}': {e}{RESET}")

def cd(args):
    target_dir = ROOT_PATH
    directory = args[0] if args else None
    if directory and directory != "~": target_dir = directory
    try: os.chdir(target_dir)
    except FileNotFoundError: print(f"{RED}Error: Directory not found: {target_dir}{RESET}")
    except NotADirectoryError: print(f"{RED}Error: Not a directory: {target_dir}{RESET}")
    except PermissionError: print(f"{RED}Error: Permission denied to change directory to '{target_dir}'.{RESET}")
    except OSError as e: print(f"{RED}Error changing directory: {e}{RESET}")

def pwd():
    try:
        cwd = os.getcwd(); display_path = ""
        root_path_abs = os.path.abspath(ROOT_PATH); cwd_abs = os.path.abspath(cwd)
        if cwd_abs == root_path_abs: display_path = "~"
        elif cwd_abs.startswith(root_path_abs + os.sep):
            relative_path = os.path.relpath(cwd_abs, root_path_abs)
            display_path = f"~/{relative_path.replace(os.sep, '/')}"
        else: display_path = cwd_abs
        print(display_path)
    except OSError as e: print(f"{RED}Error getting current directory: {e}{RESET}")

def mkdir(args):
    if not args: print("Usage: mkdir <directory>"); return
    dirname = args[0]
    try: os.makedirs(dirname, exist_ok=True); print(f"Created directory: {dirname}")
    except PermissionError: print(f"{RED}Error: Permission denied to create directory '{dirname}'.{RESET}")
    except OSError as e: print(f"{RED}Error: Could not create directory '{dirname}': {e}{RESET}")

def touch(args):
    if not args: print("Usage: touch <filename>"); return
    filename = args[0]
    try:
        if os.path.isdir(filename): print(f"{RED}Error: '{filename}' is a directory.{RESET}"); return
        parent_dir = os.path.dirname(filename)
        if parent_dir and not os.path.exists(parent_dir): os.makedirs(parent_dir, exist_ok=True)
        if os.path.exists(filename): os.utime(filename, None)
        else:
            with open(filename, 'a'): pass
    except PermissionError: print(f"{RED}Error: Permission denied for file operation on '{filename}'.{RESET}")
    except OSError as e: print(f"{RED}Error creating/updating file '{filename}': {e}{RESET}")

def move(args):
    if len(args) != 2: print("Usage: move <source> <destination>"); return
    source, destination = args[0], args[1]
    try:
        src_abs = os.path.abspath(source)
        critical_abs = [os.path.abspath(p) for p in [USER_CONFIG_FILE, REPO_FILE, MAIN_SCRIPT, APPLICATIONS_DIR]]
        if src_abs in critical_abs: print(f"{RED}Error: Cannot move critical system item '{source}' using move.{RESET}"); return
        if os.path.exists(destination) and os.path.isdir(destination) and not os.path.exists(source):
            print(f"{RED}Error: Source '{source}' not found.{RESET}"); return
        if not os.path.exists(os.path.dirname(destination)) and os.path.dirname(destination) and not (os.path.exists(destination) and os.path.isdir(destination)):
             try: os.makedirs(os.path.dirname(destination))
             except OSError as e: print(f"{RED}Error creating destination directory '{os.path.dirname(destination)}': {e}{RESET}"); return
        shutil.move(source, destination); print(f"Moved: {source} to {destination}")
    except FileNotFoundError: print(f"{RED}Error: Source '{source}' not found.{RESET}")
    except shutil.Error as e: print(f"{RED}Error moving '{source}' to '{destination}': {e}{RESET}")
    except PermissionError: print(f"{RED}Error: Permission denied during move operation.{RESET}")
    except OSError as e: print(f"{RED}Error: Could not move '{source}' to '{destination}': {e}{RESET}")

# --- Utility and External Commands ---

def help():
    print("Available commands:")
    commands = {}
    built_in_funcs = [
        ls, delf, deld, cd, pwd, mkdir, touch, move, help, clear, edit, javac,
        run, download, install, uninstall, repo, cowsay, delpanic, neofetch
    ]
    for func in built_in_funcs: commands[func.__name__] = func
    for name, info in INSTALLED_APPS.items():
        if name not in commands: commands[name] = f"Runs the '{info['name']}' application (v{info['version']})"
    if not commands: print("  (No commands available)"); return
    max_len = max(len(name) for name in commands.keys())
    for name in sorted(commands.keys()):
        obj = commands[name]
        color = GREEN if callable(obj) else BLUE
        print(f"  {color}{name:<{max_len}}{RESET} : ", end="")
        if callable(obj):
            docstring = inspect.getdoc(obj)
            if docstring:
                lines = docstring.splitlines()
                print(lines[0])
                for line in lines[1:]: print(f"    {line.strip()}")
            else: print("(No help available)")
        elif isinstance(obj, str): print(f"{PURPLE}{obj}{RESET}")
    print("\nCommands can be chained with '|' (e.g., cmd1 | cmd2)")

def clear(): os.system('cls' if os.name == 'nt' else 'clear')

def edit(args):
    if not args: print("Usage: edit <filename>"); return
    filename = args[0]
    editor = None
    if shutil.which("nano"): editor = "nano"
    elif os.name == 'nt' and shutil.which("notepad"): editor = "notepad"
    else: print(f"{RED}Error: Text editor ('nano' or 'notepad') not found in PATH.{RESET}"); return
    try:
        abs_filename = os.path.abspath(filename)
        critical_files_abs = [os.path.abspath(p) for p in [MAIN_SCRIPT]]
        if abs_filename in critical_files_abs:
            print(f"{YELLOW}Warning: Editing core OS script '{os.path.basename(filename)}'. Be careful!{RESET}")
        if not os.path.exists(abs_filename):
             parent_dir = os.path.dirname(abs_filename)
             if parent_dir and not os.path.exists(parent_dir): os.makedirs(parent_dir, exist_ok=True)
             touch([filename])
        subprocess.run([editor, abs_filename], check=(editor == "nano"))
        if abs_filename == os.path.abspath(REPO_FILE):
            print(f"{YELLOW}Repository file edited. Reloading repository...{RESET}"); load_repository()
        elif abs_filename == os.path.abspath(USER_CONFIG_FILE):
             print(f"{YELLOW}User config edited. Changes may apply on next restart.{RESET}")
             global username, hostname; _uname, _hname = load_user_config()
             if _uname and _hname: username, hostname = _uname, _hname; print(f"{GREEN}Username/Hostname reloaded.{RESET}")
        elif abs_filename.endswith("app.conf") and abs_filename.startswith(os.path.abspath(APPLICATIONS_DIR)):
             print(f"{YELLOW}Application configuration edited. Reloading applications...{RESET}"); load_applications()
    except FileNotFoundError: print(f"{RED}Error: Editor '{editor}' failed to run.{RESET}")
    except subprocess.CalledProcessError as e: print(f"{YELLOW}Editor '{editor}' closed (exit code {e.returncode}).{RESET}")
    except PermissionError: print(f"{RED}Error: Permission denied to access or modify '{filename}'.{RESET}")
    except OSError as e: print(f"{RED}Error preparing file for editing: {e}{RESET}")
    except Exception as e: print(f"{RED}An unexpected error occurred during editing: {e}{RESET}")

def download_file(url, filepath):
    print(f"Downloading {os.path.basename(url)} -> {os.path.basename(filepath)} ... ", end="", flush=True)
    try:
        parent_dir = os.path.dirname(filepath)
        if parent_dir and not os.path.exists(parent_dir): os.makedirs(parent_dir, exist_ok=True)
        headers = {'User-Agent': f'MyPythonOS Downloader/1.4 ({platform.system()}; Python/{platform.python_version()})'}
        response = requests.get(url, stream=True, headers=headers, timeout=30, allow_redirects=True)
        response.raise_for_status()
        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192): f.write(chunk)
        print(f"{GREEN}Success{RESET}"); return True
    except requests.exceptions.Timeout: print(f"{RED}Failed (Timeout){RESET}"); return False
    except requests.exceptions.RequestException as e:
        print(f"{RED}Failed ({e}){RESET}")
        if os.path.exists(filepath):
             try: os.remove(filepath)
             except OSError: pass
        return False
    except PermissionError: print(f"{RED}Failed (Permission Denied writing to '{os.path.relpath(filepath, ROOT_PATH)}'){RESET}"); return False
    except OSError as e: print(f"{RED}Failed (File System Error: {e}){RESET}"); return False
    except Exception as e:
        print(f"{RED}Failed (Unexpected Error: {e}){RESET}")
        if os.path.exists(filepath):
             try: os.remove(filepath)
             except OSError: pass
        return False

def download(args):
    if not args: print("Usage: download <url> [directory_or_filename]"); return
    url = args[0]; destination = args[1] if len(args) > 1 else None
    try:
        parsed_url = urlparse(url)
        if not parsed_url.scheme in ['http', 'https']: print(f"{RED}Error: Invalid URL scheme. Use http or https.{RESET}"); return
        filename = os.path.basename(parsed_url.path) if parsed_url.path else None
        if not filename:
             timestamp = time.strftime("%Y%m%d-%H%M%S"); filename = f"download_{timestamp}.dat"
             print(f"{YELLOW}Could not determine filename from URL. Using default: '{filename}'.{RESET}")
        filepath = ""
        if destination:
            dest_path = os.path.abspath(destination)
            if os.path.isdir(dest_path): filepath = os.path.join(dest_path, filename)
            else:
                 filepath = dest_path; dest_dir = os.path.dirname(filepath)
                 if dest_dir and not os.path.exists(dest_dir):
                     try: print(f"Creating destination directory: {os.path.relpath(dest_dir, ROOT_PATH)}"); os.makedirs(dest_dir, exist_ok=True)
                     except OSError as e: print(f"{RED}Error creating destination directory '{os.path.relpath(dest_dir, ROOT_PATH)}': {e}{RESET}"); return
        else: filepath = os.path.join(os.getcwd(), filename)
        target_path_abs = os.path.abspath(filepath)
        critical_files_abs = [os.path.abspath(p) for p in [USER_CONFIG_FILE, REPO_FILE, MAIN_SCRIPT]]
        if target_path_abs in critical_files_abs:
            print(f"{RED}Error: Cannot overwrite critical system file '{os.path.basename(filepath)}' using download.{RESET}"); return
        if os.path.exists(filepath):
            overwrite = input(f"{YELLOW}File '{os.path.relpath(filepath, ROOT_PATH)}' already exists. Overwrite? (y/N): {RESET}").lower()
            if overwrite != 'y': print("Download cancelled."); return
        download_file(url, filepath)
    except Exception as e: print(f"{RED}An unexpected error occurred during download setup: {e}{RESET}")

def javac(args):
    if not args or not args[0].endswith(".java"): print("Usage: javac <filename.java>"); return
    filename = args[0]
    try:
        if not os.path.isfile(filename): print(f"{RED}Error: Java source file not found: {filename}{RESET}"); return
        compiler = "javac"
        if not shutil.which(compiler): print(f"{RED}Error: '{compiler}' command not found (JDK required in PATH).{RESET}"); return
        print(f"Compiling {filename}...")
        result = subprocess.run([compiler, filename], check=False, capture_output=True, text=True, encoding='utf-8', errors='replace')
        if result.returncode == 0:
            print(f"{GREEN}Successfully compiled: {filename}{RESET}")
            if result.stderr: print(f"{YELLOW}Compiler Warnings:\n{result.stderr.strip()}{RESET}")
            if result.stdout: print(f"{YELLOW}Compiler Output:\n{result.stdout.strip()}{RESET}")
        else:
            print(f"{RED}Error: Compilation failed for {filename}.{RESET}")
            if result.stdout: print(f"Stdout:\n{result.stdout.strip()}")
            if result.stderr: print(f"Stderr:\n{result.stderr.strip()}")
    except Exception as e: print(f"{RED}An unexpected error occurred during Java compilation: {e}{RESET}")

def run(args):
    if not args: print("Usage: run <filename> [args...]"); return
    filename = args[0]; script_args = args[1:]; cmd = []
    try:
        if not os.path.exists(filename): print(f"{RED}Error: File not found: {filename}{RESET}"); return
        if os.path.isdir(filename): print(f"{RED}Error: Cannot run a directory: {filename}{RESET}"); return
        ext = os.path.splitext(filename)[1].lower(); abs_file_to_run = os.path.abspath(filename)
        supported = True; interpreter = None
        if ext == ".py":
            if shutil.which("python3"): interpreter = "python3"
            elif shutil.which("python"): interpreter = "python"
            else: raise FileNotFoundError("No Python interpreter ('python3' or 'python') found")
            cmd = [interpreter, abs_file_to_run] + script_args
        elif ext == ".class":
            if not shutil.which("java"): raise FileNotFoundError("'java' command not found (JRE/JDK needed)")
            class_name = os.path.splitext(os.path.basename(filename))[0]
            class_dir = os.path.dirname(abs_file_to_run)
            cmd = ["java", "-cp", class_dir, class_name] + script_args
            print(f"Attempting to run Java class: {class_name} (classpath={os.path.relpath(class_dir, ROOT_PATH)})")
        elif ext == ".lua":
             if not shutil.which("lua"): raise FileNotFoundError("'lua' command not found")
             cmd = ["lua", abs_file_to_run] + script_args
        elif ext == ".js":
            if not shutil.which("node"): raise FileNotFoundError("'node' command not found (Node.js needed)")
            cmd = ["node", abs_file_to_run] + script_args
        elif ext in [".sh", ".bash"]:
             if shutil.which("bash"): interpreter = "bash"
             elif shutil.which("sh"): interpreter = "sh"
             else: raise FileNotFoundError("No Shell interpreter ('bash' or 'sh') found")
             if os.name != 'nt' and not os.access(abs_file_to_run, os.X_OK):
                 print(f"{YELLOW}Warning: Shell script '{filename}' is not executable. Attempting to run anyway...{RESET}")
             cmd = [interpreter, abs_file_to_run] + script_args
        elif (os.name == 'nt' and ext in ['.exe', '.bat', '.cmd']) or \
             (os.name != 'nt' and os.access(abs_file_to_run, os.X_OK)):
            print(f"{YELLOW}Attempting direct execution of {filename}...{RESET}")
            cmd = [abs_file_to_run] + script_args
        else:
            supported = False
            print(f"{RED}Error: Unsupported or non-executable file type for 'run': {filename}{RESET}"); return
        if supported:
            try: cmd_str = shlex.join(cmd)
            except AttributeError: cmd_str = ' '.join([shlex.quote(p) for p in cmd])
            print(f"Running: {cmd_str}"); subprocess.run(cmd, check=True)
    except FileNotFoundError as e: print(f"{RED}Error: {e}{RESET}\nPlease ensure required interpreter is in PATH.{RESET}")
    except PermissionError: print(f"{RED}Error: Permission denied to execute '{filename}' or its interpreter.{RESET}")
    except OSError as e: print(f"{RED}Error executing '{filename}': {e}{RESET}")
    except subprocess.CalledProcessError as e: print(f"{RED}Error: Execution failed for '{filename}' (exit code {e.returncode}).{RESET}")
    except Exception as e: print(f"{RED}An unexpected error occurred while trying to run '{filename}': {e}{RESET}")

def cowsay(text_args):
    text = " ".join(text_args) if text_args else "Moo?"
    DEFAULT_WIDTH = 40
    try: max_line_len = max(10, os.get_terminal_size().columns - 6)
    except OSError: max_line_len = DEFAULT_WIDTH
    lines = []; current_line = ""
    for word in text.split():
        word_len = calculate_visual_width(word); current_len = calculate_visual_width(current_line)
        if not current_line: current_line = word
        elif current_len + word_len + 1 <= max_line_len: current_line += " " + word
        else:
            if word_len > max_line_len:
                 if current_line: lines.append(current_line)
                 lines.append(word[:max_line_len]); current_line = word[max_line_len:]
                 while len(current_line) > max_line_len: lines.append(current_line[:max_line_len]); current_line = current_line[max_line_len:]
            else: lines.append(current_line); current_line = word
    if current_line: lines.append(current_line)
    if not lines: lines.append("")
    box_width = max((calculate_visual_width(line) for line in lines), default=0)
    message = ""
    if len(lines) == 1:
        message = f"< {lines[0]} >"; top_border = f" {'_' * (box_width + 2)} "; bottom_border = f" {'-' * (box_width + 2)} "
    else:
        top_border = f" /{'-' * (box_width + 2)}\\"; bottom_border = f" \\{'-' * (box_width + 2)}/"
        message_lines = [f"| {line}{' ' * (box_width - calculate_visual_width(line))} |" for line in lines]
        message = "\n ".join(message_lines)
    cow = f"\n{top_border}\n {message}\n{bottom_border}\n        \   ^__^\n         \  (oo)\_______\n            (__)\       )\/\\\n                ||----w |\n                ||     ||\n"
    print(cow)

# --- Application Installation and Management ---

def parse_app_conf_content(content):
    conf_data = {}
    try:
        for line_num, line in enumerate(content.splitlines(), 1):
            line = line.strip().split('#', 1)[0].strip()
            if not line: continue
            if ":" in line: key, value = line.split(":", 1); conf_data[key.strip().lower()] = value.strip()
            else: print(f"{YELLOW}Warning: Malformed line {line_num} in app config (missing ':'). Ignored: '{line}'{RESET}")
    except Exception as e: print(f"{RED}Error parsing app.conf content: {e}{RESET}"); return None
    return conf_data

def install(args):
    if not args: print("Usage: install <url_or_name>\nUse 'repo list' for names."); return
    identifier = args[0]; installer_config_url = ""
    if identifier in APP_REPOSITORY:
        installer_config_url = APP_REPOSITORY[identifier]
        print(f"Found '{identifier}' in repository. Using installer: {installer_config_url}")
    else:
        installer_config_url = identifier; parsed_url = urlparse(installer_config_url)
        if not parsed_url.scheme in ['http', 'https'] or not parsed_url.netloc:
             print(f"{RED}Error: Invalid URL or unknown app name: {identifier}{RESET}"); return
        print(f"Using direct installer config URL: {installer_config_url}")

    installer_data = {}; optional_urls = []
    try:
        print(f"Fetching installer config from: {installer_config_url} ... ", end="", flush=True)
        headers = {'User-Agent': f'MyPythonOS Installer/1.4 ({platform.system()}; Python/{platform.python_version()})'}
        installer_resp = requests.get(installer_config_url, headers=headers, timeout=20, allow_redirects=True)
        installer_resp.raise_for_status(); print(f"{GREEN}Success{RESET}")
        for line_num, line in enumerate(installer_resp.text.splitlines(), 1):
            line = line.strip().split('#', 1)[0].strip()
            if not line: continue
            if ":" in line:
                key, value = map(str.strip, line.split(":", 1)); key = key.lower()
                if not value: print(f"{YELLOW}Warning: Empty value for '{key}' line {line_num} in installer. Skipping.{RESET}"); continue
                if key == "optional-url": optional_urls.append(value)
                elif key in ["folder-name", "conf-url", "script-url"]:
                    if key in installer_data: print(f"{YELLOW}Warning: Duplicate key '{key}' line {line_num} in installer. Using last.{RESET}")
                    installer_data[key] = value
                else: print(f"{YELLOW}Warning: Unknown key '{key}' line {line_num} in installer. Ignored.{RESET}")
            else: print(f"{YELLOW}Warning: Malformed line {line_num} in installer (no ':'). Ignored: '{line}'{RESET}")
        folder_name = installer_data.get("folder-name"); conf_url = installer_data.get("conf-url"); script_url = installer_data.get("script-url")
        if not all([folder_name, conf_url, script_url]):
            missing = [k for k in ['folder-name', 'conf-url', 'script-url'] if not installer_data.get(k)]
            print(f"{RED}Error: Invalid installer config. Missing: {', '.join(missing)}{RESET}"); return
    except requests.exceptions.RequestException as e: print(f"{RED}\nError: Failed to fetch installer config: {e}{RESET}"); return
    except Exception as e: print(f"{RED}\nError processing installer config: {e}{RESET}"); return

    local_conf_content = None; app_name = None; command_name = None; version = "N/A"; main_script_filename = None
    try:
        print(f"Fetching final app config from: {conf_url} ... ", end="", flush=True)
        headers = {'User-Agent': f'MyPythonOS Installer/1.4 ({platform.system()}; Python/{platform.python_version()})'}
        conf_resp = requests.get(conf_url, headers=headers, timeout=20, allow_redirects=True)
        conf_resp.raise_for_status(); local_conf_content = conf_resp.text; print(f"{GREEN}Success{RESET}")
        app_conf_data = parse_app_conf_content(local_conf_content)
        if not app_conf_data: print(f"{RED}Error: Could not parse final app config from {conf_url}{RESET}"); return
        app_name = app_conf_data.get("name"); command_name = app_conf_data.get("command", app_name)
        version = app_conf_data.get("version", "N/A"); main_script_filename = app_conf_data.get("file")
        if not all([app_name, command_name, main_script_filename]):
             missing = [k for k,v in [("'name'",app_name), ("'command'",command_name), ("'file'",main_script_filename)] if not v]
             print(f"{RED}Error: Final app config invalid. Missing: {', '.join(missing)}{RESET}"); return
        try: script_url_filename = os.path.basename(urlparse(script_url).path)
        except Exception: script_url_filename = None
        if script_url_filename and script_url_filename != main_script_filename:
             print(f"{YELLOW}Warning: Script filename from script-url ('{script_url_filename}') != 'file:' in app.conf ('{main_script_filename}'). Using app.conf value.{RESET}")
    except requests.exceptions.RequestException as e: print(f"{RED}\nError: Failed to fetch final app config from {conf_url}: {e}{RESET}"); return
    except Exception as e: print(f"{RED}\nError processing final app config: {e}{RESET}"); return

    built_in_commands = [f.__name__ for f in [ls, delf, deld, cd, pwd, mkdir, touch, move, help, clear, edit, javac, run, download, install, uninstall, repo, cowsay, delpanic, neofetch]]
    if command_name in built_in_commands: print(f"{RED}Error: Command '{command_name}' (app '{app_name}') conflicts with built-in. Aborted.{RESET}"); return
    if command_name in INSTALLED_APPS: print(f"{RED}Error: Command '{command_name}' used by '{INSTALLED_APPS[command_name]['name']}'. Aborted.{RESET}"); return

    _folder_name_parts = folder_name.replace("\\", "/").split("/")
    if any(part == ".." for part in _folder_name_parts) or \
       any(part.startswith('.') for part in _folder_name_parts if part != ".") or \
       os.path.isabs(folder_name):
        print(f"{RED}Error: Invalid folder_name '{folder_name}'. Aborted.{RESET}"); return
    app_dir = os.path.abspath(os.path.join(APPLICATIONS_DIR, folder_name))
    apps_dir_abs = os.path.abspath(APPLICATIONS_DIR)
    if not app_dir.startswith(apps_dir_abs + os.sep) and app_dir != apps_dir_abs :
        print(f"{RED}Error: folder_name '{folder_name}' resolves outside applications dir. Aborted.{RESET}"); return
    app_dir_rel = os.path.relpath(app_dir, ROOT_PATH)
    if os.path.exists(app_dir):
        overwrite = input(f"{YELLOW}App dir '{app_dir_rel}' exists. Overwrite? (y/N): {RESET}").lower()
        if overwrite == 'y':
            try: shutil.rmtree(app_dir); print(f"Removed existing: {app_dir_rel}")
            except OSError as e: print(f"{RED}Error removing existing dir: {e}. Aborted.{RESET}"); return
        else: print("Installation aborted."); return
    try: os.makedirs(app_dir, exist_ok=True); print(f"Created app directory: {app_dir_rel}")
    except OSError as e: print(f"{RED}Error creating app directory '{app_dir_rel}': {e}. Aborted.{RESET}"); return

    success = True; files_to_download = [{"url": script_url, "path": os.path.join(app_dir, main_script_filename), "optional": False}]
    for opt_url in optional_urls:
        try:
             opt_filename = os.path.basename(urlparse(opt_url).path)
             if not opt_filename: print(f"{YELLOW}Warning: No filename for optional URL: {opt_url}. Skipping.{RESET}"); continue
             if ".." in opt_filename or "/" in opt_filename or "\\" in opt_filename or opt_filename.startswith('.'):
                  print(f"{YELLOW}Warning: Skipping optional URL with unsafe filename: {opt_filename}{RESET}"); continue
             files_to_download.append({"url": opt_url, "path": os.path.join(app_dir, opt_filename), "optional": True})
        except Exception as e: print(f"{YELLOW}Warning: Error processing optional URL '{opt_url}': {e}. Skipping.{RESET}")
    downloaded_files = []
    for item in files_to_download:
        if download_file(item["url"], item["path"]): downloaded_files.append(item["path"])
        else:
            if item["optional"]: print(f"{YELLOW}Warning: Failed to download OPTIONAL: {os.path.basename(item['path'])}. Continuing.{RESET}")
            else: print(f"{RED}Failed to download REQUIRED: {os.path.basename(item['path'])}. Aborted.{RESET}"); success = False; break
    if success:
        conf_filepath = os.path.join(app_dir, "app.conf")
        try:
            with open(conf_filepath, "w", encoding='utf-8') as f: f.write(local_conf_content)
            print(f"Saved config: {os.path.basename(conf_filepath)}"); downloaded_files.append(conf_filepath)
        except OSError as e: print(f"{RED}Error saving config: {e}. Aborted.{RESET}"); success = False
    if not success:
        print(f"{RED}Installation failed. Cleaning up...{RESET}")
        try:
            if os.path.exists(app_dir): shutil.rmtree(app_dir); print(f"Removed incomplete app dir: {app_dir_rel}")
        except OSError as e: print(f"{RED}Error during cleanup: {e}{RESET}")
        return
    print(f"{GREEN}Installed '{app_name}' (cmd: {command_name} v{version}) into '{app_dir_rel}'.{RESET}")
    main_script_path = os.path.join(app_dir, main_script_filename)
    if os.path.exists(main_script_path) and os.name != 'nt':
         try: os.chmod(main_script_path, os.stat(main_script_path).st_mode | 0o100); print(f"Made '{main_script_filename}' executable.")
         except OSError as e: print(f"{YELLOW}Warning: Could not make script '{main_script_filename}' executable: {e}{RESET}")
    load_applications()

def uninstall(args):
    if not args: print("Usage: uninstall <app_command_name>\nUse 'help' for app commands."); return
    command_to_uninstall = args[0]
    if command_to_uninstall not in INSTALLED_APPS:
        print(f"{RED}Error: App command '{command_to_uninstall}' not found.{RESET}"); return
    app_info = INSTALLED_APPS[command_to_uninstall]; app_name_display = app_info['name']
    app_dir_to_delete = app_info['app_dir']; app_dir_rel_display = os.path.relpath(app_dir_to_delete, ROOT_PATH)
    print(f"{YELLOW}--- Uninstall Warning ---{RESET}")
    print(f"Uninstalling: '{app_name_display}' (command: '{command_to_uninstall}').")
    print(f"This will {RED}PERMANENTLY DELETE{RESET} its directory: {PURPLE}{app_dir_rel_display}{RESET}")
    try:
        confirm = input(f"Type 'yes' to confirm: {RESET}").strip()
        if confirm != 'yes': print("Uninstallation cancelled."); return
    except (EOFError, KeyboardInterrupt): print("\nUninstallation cancelled."); return
    print(f"\nUninstalling '{app_name_display}'...")
    try:
        if not os.path.exists(app_dir_to_delete): print(f"{YELLOW}Warning: App directory '{app_dir_rel_display}' already missing.{RESET}")
        else: shutil.rmtree(app_dir_to_delete); print(f"{GREEN}Removed app directory: '{app_dir_rel_display}'{RESET}")
        print("Reloading applications list..."); load_applications()
        if command_to_uninstall not in INSTALLED_APPS: print(f"{GREEN}App '{app_name_display}' uninstalled.{RESET}")
        else: print(f"{YELLOW}Warning: App '{command_to_uninstall}' still in list after dir removal.{RESET}")
    except OSError as e:
        print(f"{RED}Error removing app directory '{app_dir_rel_display}': {e}{RESET}")
        print(f"{YELLOW}Attempting to reload applications list anyway...{RESET}"); load_applications()
    except Exception as e:
        print(f"{RED}Unexpected error during uninstallation: {e}{RESET}"); traceback.print_exc()
        print(f"{YELLOW}Attempting to reload applications list...{RESET}"); load_applications()

def setup_app(app_dir):
    conf_file = os.path.join(app_dir, "app.conf"); app_dir_rel = os.path.relpath(app_dir, APPLICATIONS_DIR)
    try:
        with open(conf_file, "r", encoding='utf-8') as f: content = f.read()
        conf_data = parse_app_conf_content(content)
        if not conf_data: print(f"{YELLOW}Warning: Could not parse app.conf in '{app_dir_rel}'. Skipping.{RESET}"); return
        name = conf_data.get("name"); command = conf_data.get("command", name)
        version = conf_data.get("version", "N/A"); file_to_run = conf_data.get("file")
        if not all([name, command, file_to_run]):
            print(f"{YELLOW}Warning: Invalid app.conf in '{app_dir_rel}'. Missing name/command/file. Skipping.{RESET}"); return
        script_path = os.path.join(app_dir, file_to_run)
        if not os.path.exists(script_path):
            print(f"{YELLOW}Warning: Script '{file_to_run}' not found in '{app_dir_rel}' for app '{name}'. Skipping.{RESET}"); return
        built_in_commands = [f.__name__ for f in [ls, delf, deld, cd, pwd, mkdir, touch, move, help, clear, edit, javac, run, download, install, uninstall, repo, cowsay, delpanic, neofetch]]
        if command in built_in_commands:
            print(f"{YELLOW}Warning: Command '{command}' (app '{name}') conflicts with built-in. Skipping.{RESET}"); return
        if command in INSTALLED_APPS:
            existing_app_info = INSTALLED_APPS[command]
            print(f"{YELLOW}Warning: Command '{command}' conflict: App '{name}' vs '{existing_app_info['name']}'. Skipping '{name}'.{RESET}"); return
        INSTALLED_APPS[command] = {"name": name, "script": script_path, "version": version, "app_dir": app_dir}
    except OSError as e: print(f"{RED}Error reading config for app in '{app_dir_rel}': {e}{RESET}")
    except Exception as e: print(f"{RED}Error setting up app from '{app_dir_rel}': {e}{RESET}"); traceback.print_exc()

def load_applications():
    global INSTALLED_APPS; INSTALLED_APPS.clear()
    apps_dir_abs = os.path.abspath(APPLICATIONS_DIR)
    if not os.path.exists(apps_dir_abs):
        try: os.makedirs(apps_dir_abs); print(f"Created 'applications' directory."); return
        except OSError as e: print(f"{RED}Error: Could not create 'applications' directory: {e}{RESET}"); return
    app_count = 0; processed_dirs = set()
    try:
        for item_name_l1 in os.listdir(apps_dir_abs):
            path_l1 = os.path.abspath(os.path.join(apps_dir_abs, item_name_l1))
            if os.path.isdir(path_l1):
                conf_file_l1 = os.path.join(path_l1, "app.conf")
                if os.path.isfile(conf_file_l1) and path_l1 not in processed_dirs:
                    original_app_count = len(INSTALLED_APPS); setup_app(path_l1)
                    if len(INSTALLED_APPS) > original_app_count: app_count += 1
                    processed_dirs.add(path_l1)
                try:
                    for item_name_l2 in os.listdir(path_l1):
                        path_l2 = os.path.abspath(os.path.join(path_l1, item_name_l2))
                        if os.path.isdir(path_l2):
                            conf_file_l2 = os.path.join(path_l2, "app.conf")
                            if os.path.isfile(conf_file_l2) and path_l2 not in processed_dirs:
                                 original_app_count = len(INSTALLED_APPS); setup_app(path_l2)
                                 if len(INSTALLED_APPS) > original_app_count: app_count += 1
                                 processed_dirs.add(path_l2)
                except OSError as e_inner: print(f"{YELLOW}Warning: Could not list '{os.path.basename(path_l1)}': {e_inner}{RESET}")
    except OSError as e_outer: print(f"{RED}Error listing applications directory: {e_outer}{RESET}")
    except Exception as e: print(f"{RED}Unexpected error loading applications: {e}{RESET}"); traceback.print_exc()
    if app_count > 0: print(f"{GREEN}Loaded {app_count} applications.{RESET}")

def app(command, args):
    if command not in INSTALLED_APPS: print(f"{RED}Internal Error: App '{command}' not loaded.{RESET}"); return
    app_info = INSTALLED_APPS[command]; script_file = app_info["script"]; app_dir = app_info["app_dir"]
    app_dir_rel = os.path.relpath(app_dir, APPLICATIONS_DIR); cmd = []
    ext = os.path.splitext(script_file)[1].lower(); original_cwd = os.getcwd()
    try:
         os.chdir(app_dir)
         print(f"Running '{app_info['name']}' (v{app_info['version']}) from '{app_dir_rel}/'...")
         supported = True; interpreter = None
         if ext == ".py":
             if shutil.which("python3"): interpreter = "python3"
             elif shutil.which("python"): interpreter = "python"
             else: raise FileNotFoundError("No Python interpreter for app")
             cmd = [interpreter, script_file] + args
         elif ext == ".js":
             if not shutil.which("node"): raise FileNotFoundError("Node.js 'node' not found for app")
             cmd = ["node", script_file] + args
         elif ext == ".lua":
             if not shutil.which("lua"): raise FileNotFoundError("Lua 'lua' not found for app")
             cmd = ["lua", script_file] + args
         elif ext in [".sh", ".bash"]:
             if shutil.which("bash"): interpreter = "bash"
             elif shutil.which("sh"): interpreter = "sh"
             else: raise FileNotFoundError("No Shell interpreter for app")
             if os.name != 'nt' and not os.access(script_file, os.X_OK):
                 print(f"{YELLOW}Warning: App script '{os.path.basename(script_file)}' not executable. Trying anyway...{RESET}")
             cmd = [interpreter, script_file] + args
         elif (os.name == 'nt' and ext in ['.exe', '.bat', '.cmd']) or \
              (os.name != 'nt' and os.access(script_file, os.X_OK)):
             print(f"{YELLOW}Attempting direct execution of app: {os.path.basename(script_file)}...{RESET}")
             cmd = [script_file] + args
         else: supported = False; print(f"{RED}Error: Cannot run app '{app_info['name']}'. Unsupported/non-executable: {os.path.basename(script_file)}{RESET}")
         if supported:
             try: cmd_str = shlex.join(cmd)
             except AttributeError: cmd_str = ' '.join([shlex.quote(p) for p in cmd])
             print(f"Executing: {cmd_str}"); subprocess.run(cmd, check=True)
    except FileNotFoundError as e: print(f"{RED}Error running app '{app_info['name']}': {e}{RESET}")
    except PermissionError as e: print(f"{RED}Error running app '{app_info['name']}': Permission denied. {e}{RESET}")
    except OSError as e: print(f"{RED}Error executing app '{app_info['name']}': {e}{RESET}")
    except subprocess.CalledProcessError as e: print(f"{YELLOW}App '{app_info['name']}' exited non-zero ({e.returncode}).{RESET}")
    except Exception as e: print(f"{RED}Unexpected error running app '{command}': {e}{RESET}"); traceback.print_exc()
    finally:
         try: os.chdir(original_cwd)
         except OSError as cd_err:
             print(f"{RED}Error: Could not cd back to '{os.path.relpath(original_cwd, ROOT_PATH)}': {cd_err}{RESET}")
             try: os.chdir(ROOT_PATH); print(f"{YELLOW}Changed directory to root.{RESET}")
             except OSError as root_err: print(f"{RED}FATAL: Could not cd to root. CWD unknown.{RESET}")

def repo(args):
    if not args: print(f"Usage: repo list | update [<url>] | add <name> <url> | remove <name>\nDefault URL: {DEFAULT_REPO_URL}"); return
    subcommand = args[0].lower(); repo_file_path = os.path.abspath(REPO_FILE); repo_file_basename = os.path.basename(repo_file_path)
    if subcommand == "list":
        if not APP_REPOSITORY: print(f"Repository empty/not loaded. Try 'repo update' or edit '{repo_file_basename}'."); return
        print(f"--- App Repository ('{repo_file_basename}') ---")
        if not APP_REPOSITORY: print("  (empty)")
        else:
            max_name_len = max((len(name) for name in APP_REPOSITORY.keys()), default=0)
            for name, url in sorted(APP_REPOSITORY.items()): print(f"  {name:<{max_name_len}} : {url}")
            print(f"--- {len(APP_REPOSITORY)} entries ---")
    elif subcommand == "update":
        url_to_update = DEFAULT_REPO_URL
        if len(args) > 1:
            url_to_update = args[1]; parsed_url = urlparse(url_to_update)
            if not parsed_url.scheme in ['http', 'https'] or not parsed_url.netloc:
                 print(f"{RED}Error: Invalid URL: {url_to_update}{RESET}"); return
        print(f"Updating repository from: {url_to_update}")
        if download_file(url_to_update, repo_file_path):
            print(f"{GREEN}Repo file '{repo_file_basename}' updated. Reloading...{RESET}"); load_repository()
        else: print(f"{RED}Failed to update repository file.{RESET}")
    elif subcommand == "add":
        if len(args) != 3: print("Usage: repo add <name> <url>"); return
        name, url = args[1], args[2]
        if not name or ":" in name or name.startswith('#') or ' ' in name: print(f"{RED}Error: Invalid name '{name}'.{RESET}"); return
        parsed_url = urlparse(url);
        if not parsed_url.scheme in ['http', 'https'] or not parsed_url.netloc: print(f"{RED}Error: Invalid URL '{url}'.{RESET}"); return
        entry_exists = name in APP_REPOSITORY; current_url = APP_REPOSITORY.get(name)
        if entry_exists and current_url == url: print(f"{YELLOW}Entry '{name}' exists with same URL. No changes.{RESET}"); return
        elif entry_exists:
             print(f"{YELLOW}Warning: Name '{name}' exists with URL: {current_url}{RESET}")
             if input(f"Overwrite with new URL '{url}'? (y/N): ").lower() != 'y': print("Add cancelled."); return
        APP_REPOSITORY[name] = url; temp_repo_file = repo_file_path + ".tmp"
        try:
            with open(temp_repo_file, "w", encoding='utf-8') as f:
                for n, u in sorted(APP_REPOSITORY.items()): f.write(f"{n}\n{u}\n")
            shutil.move(temp_repo_file, repo_file_path)
            print(f"{GREEN}{'Updated' if entry_exists else 'Added'} '{name}' in '{repo_file_basename}'.{RESET}")
        except (OSError, IOError, shutil.Error) as e:
            print(f"{RED}Error writing repo file: {e}{RESET}\n{YELLOW}Reverting in-memory change...{RESET}")
            if entry_exists: APP_REPOSITORY[name] = current_url
            elif name in APP_REPOSITORY: del APP_REPOSITORY[name]
    elif subcommand == "remove":
        if len(args) != 2: print("Usage: repo remove <name>"); return
        name = args[1]
        if name not in APP_REPOSITORY: print(f"{RED}Error: Name '{name}' not in repository.{RESET}"); return
        removed_url = APP_REPOSITORY[name]; print(f"Removing '{name}' ({removed_url}) ...")
        del APP_REPOSITORY[name]; temp_repo_file = repo_file_path + ".tmp"
        try:
            with open(temp_repo_file, "w", encoding='utf-8') as f:
                 if APP_REPOSITORY:
                     for n, u in sorted(APP_REPOSITORY.items()): f.write(f"{n}\n{u}\n")
            shutil.move(temp_repo_file, repo_file_path)
            print(f"{GREEN}Removed '{name}' from '{repo_file_basename}'.{RESET}")
        except (OSError, IOError, shutil.Error) as e:
            print(f"{RED}Error writing repo file: {e}{RESET}\n{YELLOW}Reverting in-memory change...{RESET}")
            APP_REPOSITORY[name] = removed_url
    else: print(f"{RED}Error: Unknown repo subcommand '{subcommand}'.{RESET}")

def delpanic():
    preserve_relative = [os.path.basename(p) for p in [MAIN_SCRIPT, USER_CONFIG_FILE, REPO_FILE, APPLICATIONS_DIR]]
    preserve_absolute = [os.path.abspath(os.path.join(ROOT_PATH, p)) for p in preserve_relative]
    sentences = [ "The quick brown fox jumps over the lazy dog.", "Never gonna give you up, never gonna let you down.",
                  "All your base are belong to us.", "A penny saved is a penny earned.", "Winter is coming.",
                  "With great power comes great responsibility.", "This command will delete many files." ]
    num_confirm = min(3, len(sentences))
    if num_confirm < 3: print(f"{YELLOW}Warning: Not enough confirmation sentences.{RESET}")
    try: chosen_sentences = random.sample(sentences, num_confirm)
    except ValueError: print(f"{RED}Error selecting confirmation sentences.{RESET}"); return
    print(f"{RED}--- WARNING: DELPANIC INITIATED ---{RESET}")
    print(f"Deletes MOST files/dirs in: '{ROOT_PATH}', EXCEPT: {', '.join(preserve_relative)}")
    print(f"{RED}EXTREMELY DESTRUCTIVE and IRREVERSIBLE.{RESET}")
    print(f"{YELLOW}Type the following {num_confirm} sentences exactly (case-sensitive):{RESET}")
    for i, sentence in enumerate(chosen_sentences): print(f"  {i + 1}: {sentence}")
    for i in range(num_confirm):
        try:
            if input(f"Sentence {i + 1}/{num_confirm}: ").strip() != chosen_sentences[i]:
                print(f"{RED}Confirmation failed. Aborting DELPANIC.{RESET}"); return
        except (EOFError, KeyboardInterrupt): print(f"\n{RED}Confirmation aborted. Aborting DELPANIC.{RESET}"); return
    print(f"{GREEN}Confirmation successful. DELPANIC in 3s... (Ctrl+C to abort){RESET}")
    try: time.sleep(3)
    except KeyboardInterrupt: print(f"\n{RED}DELPANIC aborted by user.{RESET}"); return
    print(f"{RED}--- EXECUTING DELPANIC ---{RESET}")
    deleted_count, error_count, num_preserved_found = 0, 0, 0
    try: items_to_process = os.listdir(ROOT_PATH)
    except OSError as e: print(f"{RED}Fatal Error listing {ROOT_PATH}: {e}. DELPANIC aborted.{RESET}"); return
    for item_name in items_to_process:
            item_path_abs = os.path.abspath(os.path.join(ROOT_PATH, item_name))
            if item_path_abs in preserve_absolute: print(f"Skipping preserved: {item_name}"); num_preserved_found += 1; continue
            try:
                action = "Deleting file/link" if os.path.isfile(item_path_abs) or os.path.islink(item_path_abs) else \
                         "Deleting directory" if os.path.isdir(item_path_abs) else None
                if not action: print(f"{YELLOW}Skipping unknown type: {item_name}{RESET}"); continue
                print(f"{action}: {item_name} ... ", end="", flush=True)
                if os.path.isfile(item_path_abs) or os.path.islink(item_path_abs): os.remove(item_path_abs)
                elif os.path.isdir(item_path_abs): shutil.rmtree(item_path_abs)
                print(f"{GREEN}OK{RESET}"); deleted_count += 1
            except Exception as e: print(f"{RED}ERROR deleting '{item_name}': {e}{RESET}"); error_count += 1
    print(f"{GREEN}--- DELPANIC Complete ---{RESET}")
    print(f"Items attempted (excl. preserved): {len(items_to_process) - num_preserved_found}")
    print(f"Successfully deleted: {deleted_count}")
    if error_count > 0: print(f"{RED}Errors: {error_count}{RESET}")
    print(f"{YELLOW}You may need to restart the OS.{RESET}")

# --- Main Loop ---

def get_prompt(username, hostname):
    try:
        try:
            cwd = os.getcwd()
            if not os.path.exists(cwd): raise FileNotFoundError("CWD lost")
        except (FileNotFoundError, OSError) as e:
            print(f"\n{YELLOW}Warning: CWD lost or invalid ({e}). Returning to root.{RESET}")
            os.chdir(ROOT_PATH); cwd = ROOT_PATH
        display_path = ""; root_path_abs = os.path.abspath(ROOT_PATH); cwd_abs = os.path.abspath(cwd)
        if cwd_abs == root_path_abs: display_path = "~"
        elif cwd_abs.startswith(root_path_abs + os.sep):
             relative_path = os.path.relpath(cwd_abs, root_path_abs)
             display_path = f"~/{relative_path.replace(os.sep, '/')}"
        else: display_path = cwd_abs # Show full path if outside root
        return f"{GREEN}{username}@{hostname}{RESET}:{BLUE}{display_path}{RESET} $ "
    except OSError as e:
         print(f"\n{RED}Error getting prompt: {e}. Basic prompt.{RESET}")
         return f"{GREEN}{username}@{hostname}{RESET}:{RED}???{RESET} $ "

def run_single_command(cmd, args):
    command_map = {
        "help": help, "clear": clear, "neofetch": neofetch, "ls": ls, "delf": delf, "deld": deld,
        "cd": cd, "pwd": pwd, "mkdir": mkdir, "touch": touch, "move": move, "edit": edit,
        "javac": javac, "run": run, "download": download, "install": install, "uninstall": uninstall,
        "repo": repo, "cowsay": cowsay, "delpanic": delpanic,
    }
    if cmd == "exit": print("Exiting MyPythonOS..."); return False
    target_func = command_map.get(cmd)
    if target_func:
        try:
            sig = inspect.signature(target_func)
            if not sig.parameters:
                if args: pass # print(f"{YELLOW}Warning: '{cmd}' ignores args.{RESET}")
                target_func()
            else: target_func(args)
        except TypeError as te: print(f"{RED}Error executing '{cmd}': {te}\n{YELLOW}Usage incorrect? Try 'help {cmd}'.{RESET}")
        except Exception as e: print(f"\n{RED}--- ERROR IN CMD '{cmd}' ---{RESET}"); traceback.print_exc(); print(f"{YELLOW}Cmd '{cmd}' failed.{RESET}")
    elif cmd in INSTALLED_APPS:
        try: app(cmd, args)
        except Exception as e: print(f"\n{RED}--- ERROR RUNNING APP '{cmd}' ---{RESET}"); traceback.print_exc(); print(f"{YELLOW}App '{cmd}' failed.{RESET}")
    else: print(f"{RED}Command not found: {cmd}{RESET}")
    return True

def main():
    global ROOT_PATH, username, hostname

    # Print readline status early, after colors are defined.
    if readline is None:
        print(f"{YELLOW}Warning: readline library not found. Command history and advanced line editing will not be available.{RESET}")
        print(f"{YELLOW}  On Linux/macOS, ensure 'readline' is installed (often system-provided or via package manager).{RESET}")
        print(f"{YELLOW}  On Windows, try: pip install pyreadline3{RESET}")
    elif 'pyreadline3' in str(readline): # Check if it's pyreadline3
         print(f"{YELLOW}Using pyreadline3 for history/input on Windows.{RESET}")


    if readline and hasattr(readline, "read_history_file"):
        try:
            readline.read_history_file(HISTORY_FILE)
            if hasattr(readline, "set_history_length"): # pyreadline3 might not have this
                readline.set_history_length(HISTORY_MAX_LINES)
        except FileNotFoundError: pass
        except Exception as e: print(f"{YELLOW}Warning: Could not load command history: {e}{RESET}")

    clear()
    print(f"Welcome to MyPythonOS!")
    try: os.makedirs(APPLICATIONS_DIR, exist_ok=True)
    except OSError as e: print(f"{RED}Fatal: Could not create '{APPLICATIONS_DIR}': {e}{RESET}"); return
    print(f"Root directory: {ROOT_PATH}\nType 'help' for commands, 'exit' to quit.\nCommands can be chained with '|'.\n" + "-" * 30)

    _uname, _hname = load_user_config()
    if not _uname or not _hname:
        print("Performing first-time user setup..."); _uname, _hname = create_user_config()
        if not _uname or not _hname: print(f"{RED}Failed to create user config. Exiting.{RESET}"); return
        print("-" * 30)
    username, hostname = _uname, _hname

    if not os.path.exists(REPO_FILE):
        print(f"Repository file '{os.path.basename(REPO_FILE)}' not found.")
        download_repo = ""
        try: download_repo = input(f"Download initial repository from default URL? (Y/n): ").lower()
        except (EOFError, KeyboardInterrupt): print("\nSkipping repository download."); download_repo = 'n'
        if download_repo == "" or download_repo == "y":
            print(f"Attempting to download initial repository...")
            if download_file(DEFAULT_REPO_URL, REPO_FILE): print(f"{GREEN}Successfully downloaded initial repository.{RESET}")
            else: print(f"{YELLOW}Warning: Failed to download initial repository.\nUse 'repo update' or create '{os.path.basename(REPO_FILE)}' manually.{RESET}")
        else: print(f"Skipping repository download. Use 'repo update' later.")
        print("-" * 30)

    load_repository(); load_applications(); print("-" * 30)
    try: os.chdir(ROOT_PATH)
    except OSError as e: print(f"{RED}Fatal: Could not change to root '{ROOT_PATH}': {e}{RESET}"); return

    running = True; last_command = ""
    while running:
        try:
            prompt_str = get_prompt(username, hostname)
            command_line = input(prompt_str).strip()
            if not command_line: continue
            if readline and command_line != last_command and hasattr(readline, "add_history"):
                readline.add_history(command_line)
                last_command = command_line
            command_sequence = [cmd.strip() for cmd in command_line.split('|') if cmd.strip()]
            for single_command_str in command_sequence:
                try: parts = shlex.split(single_command_str)
                except ValueError as e: print(f"{RED}Error parsing '{single_command_str}': {e}\n{YELLOW}Check quoting. Skipping.{RESET}"); continue
                if not parts: continue
                cmd, args = parts[0], parts[1:]
                running = run_single_command(cmd, args)
                if not running: break
        except KeyboardInterrupt: print("\n^C")
        except EOFError: print("\nexit"); running = False
        except Exception as e:
            print(f"\n{RED}--- UNEXPECTED OS ERROR ---{RESET}\n{RED}Critical error in main loop:{RESET}"); traceback.print_exc()
            print(f"{YELLOW}Attempting to recover...{RESET}")
            try: os.chdir(ROOT_PATH); print(f"{YELLOW}Returned to root.{RESET}")
            except Exception as chdir_err: print(f"{RED}FATAL: Could not return to root: {chdir_err}. Exiting.{RESET}"); running = False

    if readline and hasattr(readline, "write_history_file"):
        try: readline.write_history_file(HISTORY_FILE)
        except Exception as e: print(f"{YELLOW}Warning: Could not save command history: {e}{RESET}")

if __name__ == "__main__":
    main()
    print(f"{ORANGE}MyPythonOS session ended.{RESET}")
