# --- 1. Install System Dependencies ---
# This installs Python, pip, and other tools your script uses like
# requests, Java (javac/java), Go, and NodeJS.
echo "--- Installing system dependencies... ---"
apk update
apk add python3 py3-pip py3-requests py3-readline build-base openjdk17-jdk go nodejs lua

echo "--- Dependencies installed. ---"

# --- 2. Create the nullos.py Script ---
# This uses a 'here document' to write your Python code directly into the file.
# No interactive editor is needed.
echo "--- Creating /usr/local/bin/nullos.py... ---"
cat << 'EOF' > /usr/local/bin/nullos.py
#!/usr/bin/env python3
# main.py
import os
import platform
import shutil
import json
import inspect
import subprocess
import requests
from urllib.parse import urlparse
import time
import random
import traceback
import shlex
import re

# Attempt to import readline for command history and better input
try:
    import readline
except ImportError:
    try:
        import pyreadline3 as readline  # For Windows
    except ImportError:
        readline = None  # No readline library found


class MyPythonOS:
    """
    A class that encapsulates the entire state and functionality of a simple,
    Python-based terminal "Operating System".
    """

    # --- Core Class Setup & Constants ---

    def __init__(self, library_mode=False):
        """Initializes the OS, setting up paths, colors, and loading all configurations."""
        self.library_mode = library_mode
        # ANSI escape codes for colors
        self.RED = '\033[91m'
        self.ORANGE = '\033[38;5;208m'
        self.YELLOW = '\033[93m'
        self.GREEN = '\033[92m'
        self.BLUE = '\033[94m'
        self.PURPLE = '\033[95m'
        self.RESET = '\033[0m'

        # --- System Paths and Files ---
        self.ROOT_PATH = os.path.abspath("./")
        self.USER_CONFIG_FILE = os.path.join(self.ROOT_PATH, "user.json")
        self.APPLICATIONS_DIR = os.path.join(self.ROOT_PATH, "applications")
        self.REPO_FILE = os.path.join(self.ROOT_PATH, "repo.txt")
        self.HISTORY_FILE = os.path.join(self.ROOT_PATH, ".mypythos_history")
        try:
            self.MAIN_SCRIPT = os.path.basename(__file__)
        except NameError:
            self.MAIN_SCRIPT = "mypythonos_script.py"

        # --- Constants ---
        self.DEFAULT_REPO_URL = "https://raw.githubusercontent.com/AxoIsAxo/null.os/refs/heads/main/repo.txt"
        self.HISTORY_MAX_LINES = 1000

        # --- System State ---
        self.username = "user"
        self.hostname = "mypythos"
        self.installed_apps = {}
        self.app_repository = {}
        self.running = True

        # --- Start Initialization Sequence ---
        if not self.library_mode:
            self._setup_readline()
            self.cmd_clear()
            print("Welcome to MyPythonOS!")

        self._initialize_filesystem()
        self._load_user_config()
        self._load_repository()
        self._load_applications()

        try:
            os.chdir(self.ROOT_PATH)
        except OSError as e:
            if not self.library_mode:
                print(f"{self.RED}Fatal: Could not change to root '{self.ROOT_PATH}': {e}{self.RESET}")
            self.running = False
        
        if not self.library_mode:
            print("-" * 30)
            print(f"Root directory: {self.ROOT_PATH}\nType 'help' for commands, 'exit' to quit.\nCommands can be chained with '|'.")
            print("-" * 30)

    # --- System Initialization and Loading ---

    def _setup_readline(self):
        """Configures the readline library for command history."""
        if readline is None:
            print(f"{self.YELLOW}Warning: readline not found. Command history and advanced line editing are disabled.{self.RESET}")
            print(f"{self.YELLOW}  On Windows, try: pip install pyreadline3{self.RESET}")
            return

        print(f"{self.YELLOW}Readline support enabled for command history.{self.RESET}")
        try:
            if os.path.exists(self.HISTORY_FILE):
                readline.read_history_file(self.HISTORY_FILE)
            if hasattr(readline, "set_history_length"):
                readline.set_history_length(self.HISTORY_MAX_LINES)
        except Exception as e:
            print(f"{self.YELLOW}Warning: Could not load command history: {e}{self.RESET}")

    def _initialize_filesystem(self):
        """Ensures that essential directories like 'applications' exist."""
        try:
            os.makedirs(self.APPLICATIONS_DIR, exist_ok=True)
        except OSError as e:
            if not self.library_mode:
                print(f"{self.RED}Fatal: Could not create '{self.APPLICATIONS_DIR}': {e}{self.RESET}")
            self.running = False

    def _load_user_config(self):
        """Loads user config from user.json, or creates it if it doesn't exist."""
        if os.path.exists(self.USER_CONFIG_FILE):
            try:
                with open(self.USER_CONFIG_FILE, "r") as f:
                    config = json.load(f)
                self.username = config.get("username", "user")
                self.hostname = config.get("hostname", "hostname")
            except json.JSONDecodeError:
                if not self.library_mode:
                    print(f"{self.YELLOW}Warning: Could not decode user.json. Using defaults.{self.RESET}")
        else:
            if not self.library_mode:
                print("Performing first-time user setup...")
            self._create_user_config()
        if not self.library_mode:
            print("-" * 30)

    def _create_user_config(self):
        """Prompts for and saves a new user configuration."""
        if self.library_mode:
            _username, _hostname = "user", "mypythos"
        else:
            _username = input("Enter username: ").strip() or "user"
            _hostname = input("Enter hostname: ").strip() or "mypythos"
            
        self.username, self.hostname = _username, _hostname
        config = {"username": self.username, "hostname": self.hostname}
        try:
            with open(self.USER_CONFIG_FILE, "w") as f:
                json.dump(config, f, indent=4)
            if not self.library_mode:
                print(f"{self.GREEN}User configuration saved to user.json{self.RESET}")
        except OSError as e:
            if not self.library_mode:
                print(f"{self.RED}Error: Could not create user.json: {e}{self.RESET}")
            self.username, self.hostname = "user", "mypythos"

    def _load_repository(self):
        """Loads the application repository from repo.txt, downloading it if necessary."""
        self.app_repository.clear()
        if not os.path.exists(self.REPO_FILE) and not self.library_mode:
            print(f"Repository file '{os.path.basename(self.REPO_FILE)}' not found.")
            try:
                download_repo = input(f"Download initial repository from default URL? (Y/n): ").lower()
            except (EOFError, KeyboardInterrupt):
                print("\nSkipping repository download.")
                return
            if download_repo in ["", "y"]:
                print("Attempting to download initial repository...")
                if self._download_file(self.DEFAULT_REPO_URL, self.REPO_FILE):
                    print(f"{self.GREEN}Successfully downloaded initial repository.{self.RESET}")
                else:
                    print(f"{self.YELLOW}Warning: Failed to download repository.{self.RESET}")
            else:
                print("Skipping repository download. Use 'repo update' later.")
        
        if not os.path.exists(self.REPO_FILE):
            return
        
        try:
            with open(self.REPO_FILE, "r") as f:
                lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            if len(lines) % 2 != 0:
                if not self.library_mode: print(f"{self.YELLOW}Warning: Malformed repo file. Ignoring last.{self.RESET}")
                lines = lines[:-1]
            
            for i in range(0, len(lines), 2):
                name, url = lines[i], lines[i+1]
                if name and url: self.app_repository[name] = url
            
            if self.app_repository and not self.library_mode:
                print(f"{self.GREEN}Loaded {len(self.app_repository)} entries from repository.{self.RESET}")
        except OSError as e:
            if not self.library_mode: print(f"{self.RED}Error reading repository file: {e}{self.RESET}")

    def _load_applications(self):
        """Scans the applications directory and loads all valid installed apps."""
        self.installed_apps.clear()
        if not os.path.isdir(self.APPLICATIONS_DIR):
            return

        app_count = 0
        for item_name in os.listdir(self.APPLICATIONS_DIR):
            app_dir = os.path.join(self.APPLICATIONS_DIR, item_name)
            if os.path.isdir(app_dir):
                if os.path.isfile(os.path.join(app_dir, "app.conf")):
                    if self._setup_app(app_dir):
                        app_count += 1
        
        if app_count > 0 and not self.library_mode:
            print(f"{self.GREEN}Loaded {app_count} applications.{self.RESET}")

    def _setup_app(self, app_dir):
        """Reads an app.conf file and registers the application if valid."""
        conf_file = os.path.join(app_dir, "app.conf")
        app_dir_rel = os.path.relpath(app_dir, self.APPLICATIONS_DIR)
        try:
            with open(conf_file, "r", encoding='utf-8') as f:
                content = f.read()
            conf_data = self._parse_app_conf_content(content)

            if not conf_data: return False

            name = conf_data.get("name")
            command = conf_data.get("command", name)
            version = conf_data.get("version", "N/A")
            file_to_run = conf_data.get("file")

            if not all([name, command, file_to_run]): return False

            script_path = os.path.join(app_dir, file_to_run)
            if not os.path.isfile(script_path): return False
            
            if hasattr(self, f"cmd_{command}") or command in self.installed_apps: return False
            
            self.installed_apps[command] = {"name": name, "script": script_path, "version": version, "app_dir": app_dir}
            return True
        except Exception:
            return False

    # --- Command Implementations: File System ---

    def cmd_ls(self, args=None):
        """(ls) Lists files and directories. Use 'ls -l' for detailed view."""
        if args is None: args = []
        try:
            detailed = "-l" in args
            target_dir = os.getcwd()
            items = sorted(os.listdir(target_dir))
            for item in items:
                try:
                    item_path = os.path.join(target_dir, item)
                    if detailed:
                        stat_info = os.stat(item_path)
                        size = stat_info.st_size
                        if os.path.isdir(item_path): print(f"{self.BLUE}d {size:>10} {item}/{self.RESET}")
                        else: print(f"- {size:>10} {item}{self.RESET}")
                    else:
                        if os.path.isdir(item_path): print(f"{self.BLUE}{item}{self.RESET}/")
                        elif os.path.isfile(item_path): print(item)
                        else: print(f"{self.ORANGE}{item}{self.RESET}")
                except OSError: print(f"{self.RED}Error reading: {item}{self.RESET}")
        except FileNotFoundError: print(f"{self.RED}Error: Directory not found.{self.RESET}")
        except OSError as e: print(f"{self.RED}Error listing directory: {e}{self.RESET}")

    def cmd_cd(self, args):
        """(cd) Changes the current directory. 'cd ~' or 'cd' goes to root."""
        target_dir = args[0] if args and args[0] != "~" else self.ROOT_PATH
        try:
            os.chdir(target_dir)
        except FileNotFoundError: print(f"{self.RED}Error: Directory not found: {target_dir}{self.RESET}")
        except NotADirectoryError: print(f"{self.RED}Error: Not a directory: {target_dir}{self.RESET}")
        except OSError as e: print(f"{self.RED}Error changing directory: {e}{self.RESET}")

    def cmd_pwd(self, args=None):
        """(pwd) Prints the current working directory path."""
        try:
            cwd_abs = os.path.abspath(os.getcwd())
            root_abs = os.path.abspath(self.ROOT_PATH)
            if cwd_abs == root_abs:
                print("~")
            elif cwd_abs.startswith(root_abs + os.sep):
                print(f"~/{os.path.relpath(cwd_abs, root_abs).replace(os.sep, '/')}")
            else:
                print(cwd_abs)
        except OSError as e: print(f"{self.RED}Error getting current directory: {e}{self.RESET}")

    def cmd_mkdir(self, args):
        """(mkdir) Creates a new directory."""
        if not args: print("Usage: mkdir <directory_name>"); return
        try:
            os.makedirs(args[0], exist_ok=True)
            print(f"Created directory: {args[0]}")
        except OSError as e: print(f"{self.RED}Error: Could not create directory: {e}{self.RESET}")

    def cmd_touch(self, args):
        """(touch) Creates an empty file or updates its timestamp."""
        if not args: print("Usage: touch <filename>"); return
        filename = args[0]
        try:
            if os.path.isdir(filename): print(f"{self.RED}Error: '{filename}' is a directory.{self.RESET}"); return
            with open(filename, 'a'):
                os.utime(filename, None)
        except OSError as e: print(f"{self.RED}Error creating/updating file: {e}{self.RESET}")

    def cmd_move(self, args):
        """(move) Moves or renames a file or directory."""
        if len(args) != 2: print("Usage: move <source> <destination>"); return
        source, destination = args
        try:
            critical_paths = [os.path.abspath(p) for p in [self.USER_CONFIG_FILE, self.REPO_FILE, self.MAIN_SCRIPT, self.APPLICATIONS_DIR]]
            if os.path.abspath(source) in critical_paths:
                print(f"{self.RED}Error: Cannot move a critical system item '{source}'.{self.RESET}")
                return
            shutil.move(source, destination)
            print(f"Moved: {source} -> {destination}")
        except FileNotFoundError: print(f"{self.RED}Error: Source '{source}' not found.{self.RESET}")
        except shutil.Error as e: print(f"{self.RED}Error moving item: {e}{self.RESET}")

    def cmd_delf(self, args):
        """(delf) Deletes a file."""
        if not args: print("Usage: delf <filename>"); return
        filename = args[0]
        try:
            critical_files = [os.path.abspath(p) for p in [self.USER_CONFIG_FILE, self.REPO_FILE, self.MAIN_SCRIPT]]
            if os.path.abspath(filename) in critical_files:
                print(f"{self.RED}Error: Cannot delete critical system file '{os.path.basename(filename)}'.{self.RESET}"); return
            os.remove(filename)
            print(f"Deleted file: {filename}")
        except FileNotFoundError: print(f"{self.RED}Error: File not found: {filename}{self.RESET}")
        except IsADirectoryError: print(f"{self.RED}Error: '{filename}' is a directory. Use 'deld'.{self.RESET}")
        except OSError as e: print(f"{self.RED}Error deleting file: {e}{self.RESET}")

    def cmd_deld(self, args):
        """(deld) Deletes a directory and its contents."""
        if not args: print("Usage: deld <directory_name>"); return
        dirname = args[0]
        try:
            target_path = os.path.abspath(dirname)
            if target_path in [os.path.abspath(self.ROOT_PATH), os.path.abspath(self.APPLICATIONS_DIR)]:
                 print(f"{self.RED}Error: Cannot delete protected directory '{os.path.basename(dirname)}'.{self.RESET}"); return
            if target_path == os.path.abspath(os.getcwd()):
                 print(f"{self.RED}Error: Cannot delete the current working directory.{self.RESET}"); return

            shutil.rmtree(dirname)
            print(f"Deleted directory: {dirname}")
        except FileNotFoundError: print(f"{self.RED}Error: Directory not found: {dirname}{self.RESET}")
        except NotADirectoryError: print(f"{self.RED}Error: '{dirname}' is not a directory.{self.RESET}")
        except OSError as e: print(f"{self.RED}Error deleting directory: {e}{self.RESET}")
        
    def cmd_delpanic(self, args=None):
        """(delpanic) EXTREMELY DESTRUCTIVE. Deletes all non-essential files in the root directory."""
        preserve_relative = [os.path.basename(p) for p in [self.MAIN_SCRIPT, self.USER_CONFIG_FILE, self.REPO_FILE, self.APPLICATIONS_DIR]]
        preserve_absolute = [os.path.abspath(p) for p in preserve_relative]
        
        sentences = ["All your base are belong to us.", "This command will delete many files."]
        
        print(f"{self.RED}--- WARNING: DELPANIC INITIATED ---{self.RESET}")
        print(f"This will delete MOST files/dirs in the root, EXCEPT: {', '.join(preserve_relative)}")
        print(f"{self.RED}This action is IRREVERSIBLE.{self.RESET}")
        
        try:
            chosen_sentence = random.choice(sentences)
            print(f"{self.YELLOW}To confirm, type this sentence exactly:{self.RESET}\n  {chosen_sentence}")
            if input("> ").strip() != chosen_sentence:
                print(f"{self.RED}Confirmation failed. Aborting DELPANIC.{self.RESET}"); return
        except (EOFError, KeyboardInterrupt):
            print(f"\n{self.RED}Confirmation aborted. Aborting DELPANIC.{self.RESET}"); return

        print(f"{self.GREEN}Confirmation successful. Proceeding...{self.RESET}")
        deleted_count, error_count = 0, 0
        
        for item_name in os.listdir(self.ROOT_PATH):
            item_path = os.path.abspath(os.path.join(self.ROOT_PATH, item_name))
            if item_path in preserve_absolute:
                print(f"Skipping preserved: {item_name}")
                continue
            
            try:
                print(f"Deleting: {item_name} ... ", end="", flush=True)
                if os.path.isdir(item_path): shutil.rmtree(item_path)
                else: os.remove(item_path)
                print(f"{self.GREEN}OK{self.RESET}"); deleted_count += 1
            except Exception as e:
                print(f"{self.RED}ERROR: {e}{self.RESET}"); error_count += 1

        print(f"{self.GREEN}--- DELPANIC Complete ---{self.RESET}")
        print(f"Successfully deleted: {deleted_count}. Errors: {error_count}.")

    # --- Command Implementations: Applications & Packages ---

    def cmd_install(self, args):
        """(install) Installs an application from a URL or repository name."""
        if not args: print("Usage: install <url_or_name>\nUse 'repo list' for names."); return
        identifier = args[0]
        
        if identifier in self.app_repository:
            installer_config_url = self.app_repository[identifier]
            print(f"Found '{identifier}' in repository. Using: {installer_config_url}")
        else:
            installer_config_url = identifier
            if not urlparse(installer_config_url).scheme in ['http', 'https']:
                 print(f"{self.RED}Error: Invalid URL or unknown app name: {identifier}{self.RESET}"); return
            print(f"Using direct installer config URL: {installer_config_url}")
        
        try:
            print("Fetching installer config... ", end="", flush=True)
            installer_resp = requests.get(installer_config_url, timeout=20, allow_redirects=True)
            installer_resp.raise_for_status()
            
            installer_data = {}
            optional_urls = []
            for line in installer_resp.text.splitlines():
                line = line.strip().split('#', 1)[0].strip()
                if ":" in line:
                    key, value = map(str.strip, line.split(":", 1))
                    key = key.lower()
                    if key == "optional-url": optional_urls.append(value)
                    else: installer_data[key] = value

            print(f"{self.GREEN}Success{self.RESET}")
            
            folder_name = installer_data.get("folder-name")
            conf_url = installer_data.get("conf-url")
            script_url = installer_data.get("script-url")
            if not all([folder_name, conf_url, script_url]):
                print(f"{self.RED}Error: Installer config is missing required fields.{self.RESET}"); return
        except Exception as e:
            print(f"{self.RED}\nError: Failed to fetch or parse installer: {e}{self.RESET}"); return
        
        try:
            print("Fetching final app config... ", end="", flush=True)
            conf_resp = requests.get(conf_url, timeout=20, allow_redirects=True)
            conf_resp.raise_for_status()
            final_conf_content = conf_resp.text
            final_conf_data = self._parse_app_conf_content(final_conf_content)
            print(f"{self.GREEN}Success{self.RESET}")

            app_name = final_conf_data.get("name")
            command = final_conf_data.get("command", app_name)
            if not app_name or not command:
                print(f"{self.RED}Error: Final app config is invalid.{self.RESET}"); return
            if hasattr(self, f"cmd_{command}") or command in self.installed_apps:
                print(f"{self.RED}Error: App command '{command}' conflicts with existing command.{self.RESET}"); return
        except Exception as e:
            print(f"{self.RED}\nError: Failed to fetch final app config: {e}{self.RESET}"); return

        app_dir = os.path.join(self.APPLICATIONS_DIR, folder_name)
        if os.path.exists(app_dir):
            if input(f"{self.YELLOW}App dir '{os.path.relpath(app_dir)}' exists. Overwrite? (y/N): {self.RESET}").lower() != 'y':
                print("Installation aborted."); return
            try: shutil.rmtree(app_dir)
            except OSError as e: print(f"{self.RED}Error removing existing dir: {e}. Aborted.{self.RESET}"); return
        
        try:
            os.makedirs(app_dir, exist_ok=True)
            
            files_to_download = []
            main_script_filename = os.path.basename(urlparse(script_url).path)
            files_to_download.append({"url": script_url, "path": os.path.join(app_dir, main_script_filename), "optional": False})
            
            for opt_url in optional_urls:
                opt_filename = os.path.basename(urlparse(opt_url).path)
                if not opt_filename or ".." in opt_filename or "/" in opt_filename or "\\" in opt_filename: continue
                files_to_download.append({"url": opt_url, "path": os.path.join(app_dir, opt_filename), "optional": True})
            
            installation_success = True
            for file_item in files_to_download:
                if not self._download_file(file_item["url"], file_item["path"]):
                    if file_item["optional"]:
                        print(f"{self.YELLOW}Warning: Failed to download OPTIONAL file. Continuing...{self.RESET}")
                    else:
                        print(f"{self.RED}Error: Failed to download REQUIRED file. Aborting.{self.RESET}")
                        installation_success = False; break 

            if not installation_success: raise IOError("A required file failed to download.")

            with open(os.path.join(app_dir, "app.conf"), "w", encoding='utf-8') as f:
                f.write(final_conf_content)

            print(f"{self.GREEN}Successfully installed '{app_name}' (command: {command}).{self.RESET}")
            self._load_applications()

        except Exception as e:
            print(f"{self.RED}Installation failed: {e}. Cleaning up...{self.RESET}")
            if os.path.exists(app_dir): shutil.rmtree(app_dir)

    def cmd_uninstall(self, args):
        """(uninstall) Removes an installed application."""
        if not args: print("Usage: uninstall <app_command_name>"); return
        command = args[0]
        if command not in self.installed_apps:
            print(f"{self.RED}Error: App command '{command}' not found.{self.RESET}"); return
        
        app_info = self.installed_apps[command]
        app_dir = app_info['app_dir']
        print(f"{self.YELLOW}--- Uninstall Warning ---{self.RESET}")
        print(f"This will {self.RED}PERMANENTLY DELETE{self.RESET} the app '{app_info['name']}'")
        print(f"and its directory: {self.PURPLE}{os.path.relpath(app_dir)}{self.RESET}")
        
        try:
            if input("Type 'yes' to confirm: ").strip() != 'yes':
                print("Uninstallation cancelled."); return
        except (EOFError, KeyboardInterrupt): print("\nUninstallation cancelled."); return

        try:
            shutil.rmtree(app_dir)
            print(f"{self.GREEN}Successfully uninstalled '{app_info['name']}'.{self.RESET}")
            self._load_applications()
        except OSError as e:
            print(f"{self.RED}Error removing app directory: {e}{self.RESET}")

    def cmd_repo(self, args):
        """(repo) Manages the application repository. Use 'repo list|update|add|remove'."""
        if not args: print("Usage: repo <list|update|add|remove> [options]"); return
        subcommand = args[0].lower()
        
        if subcommand == "list":
            if not self.app_repository: print("Repository is empty."); return
            print(f"--- App Repository ('{os.path.basename(self.REPO_FILE)}') ---")
            max_len = max((len(k) for k in self.app_repository.keys()), default=0)
            for name, url in sorted(self.app_repository.items()):
                print(f"  {name:<{max_len}} : {url}")
        
        elif subcommand == "update":
            url = args[1] if len(args) > 1 else self.DEFAULT_REPO_URL
            print(f"Updating repository from: {url}")
            if self._download_file(url, self.REPO_FILE):
                print(f"{self.GREEN}Repository file updated. Reloading...{self.RESET}")
                self._load_repository()
            else:
                print(f"{self.RED}Failed to update repository.{self.RESET}")
        
        elif subcommand == "add":
            if len(args) != 3: print("Usage: repo add <name> <url>"); return
            name, url = args[1], args[2]
            if name in self.app_repository:
                print(f"{self.YELLOW}Warning: Name '{name}' already exists.{self.RESET}")
                return
            self.app_repository[name] = url
            self._save_repository()
            print(f"{self.GREEN}Added '{name}' to repository.{self.RESET}")

        elif subcommand == "remove":
            if len(args) != 2: print("Usage: repo remove <name>"); return
            name = args[1]
            if name not in self.app_repository:
                print(f"{self.RED}Error: Name '{name}' not in repository.{self.RESET}"); return
            del self.app_repository[name]
            self._save_repository()
            print(f"{self.GREEN}Removed '{name}' from repository.{self.RESET}")
        
        else:
            print(f"{self.RED}Error: Unknown repo subcommand '{subcommand}'.{self.RESET}")

    # --- Command Implementations: Execution & Utility ---

    def cmd_help(self, args=None):
        """(help) Shows this help message."""
        print("Available commands:")
        
        command_methods = [m for m in dir(self) if m.startswith('cmd_') and callable(getattr(self, m))]
        
        commands = {}
        for method_name in sorted(command_methods):
            cmd_name = method_name.replace('cmd_', '')
            func = getattr(self, method_name)
            doc = inspect.getdoc(func) or "(No description available)"
            commands[cmd_name] = f"{self.GREEN}{doc}{self.RESET}"

        for name, info in sorted(self.installed_apps.items()):
            commands[name] = f"{self.BLUE}Runs the '{info['name']}' application (v{info['version']}){self.RESET}"
            
        max_len = max((len(name) for name in commands.keys()), default=0)
        for name, desc in commands.items():
            print(f"  {name:<{max_len}} : {desc}")

        print("\nCommands can be chained with '|' (e.g., ls -l | cowsay)")

    def cmd_clear(self, args=None):
        """(clear) Clears the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')

    def cmd_edit(self, args):
            """(edit) Opens a file in a system text editor (nano/notepad)."""
            if not args: print("Usage: edit <filename>"); return
            filename = args[0]
            editor = shutil.which("nano") or (shutil.which("notepad") if os.name == 'nt' else None)
            if not editor:
                print(f"{self.RED}Error: Text editor ('nano' or 'notepad') not found.{self.RESET}"); return
            
            try:
                if not os.path.exists(filename):
                    parent_dir = os.path.dirname(filename)
                    if parent_dir: os.makedirs(parent_dir, exist_ok=True)
                    open(filename, 'a').close()
                
                subprocess.run([editor, filename])
            except KeyboardInterrupt:
                print("\n^C (Editor closed)")
            except Exception as e:
                print(f"{self.RED}An unexpected error occurred during editing: {e}{self.RESET}")
    
    def cmd_download(self, args):
        """(download) Downloads a file from a URL."""
        if not args: print("Usage: download <url> [destination]"); return
        url, dest = args[0], args[1] if len(args) > 1 else None
        
        try:
            filename = os.path.basename(urlparse(url).path) or f"download_{int(time.time())}.dat"
            filepath = os.path.join(dest, filename) if dest and os.path.isdir(dest) else dest or filename

            if os.path.abspath(filepath) in [os.path.abspath(f) for f in [self.USER_CONFIG_FILE, self.REPO_FILE, self.MAIN_SCRIPT]]:
                print(f"{self.RED}Error: Cannot overwrite a critical system file.{self.RESET}"); return
            
            if os.path.exists(filepath):
                if input(f"{self.YELLOW}File '{filepath}' exists. Overwrite? (y/N): {self.RESET}").lower() != 'y':
                    print("Download cancelled."); return

            self._download_file(url, filepath)
        except Exception as e:
            print(f"{self.RED}An unexpected error occurred: {e}{self.RESET}")
            
    def cmd_javac(self, args):
        """(javac) Compiles a .java file into a .class file."""
        if not args or not args[0].endswith(".java"): print("Usage: javac <filename.java>"); return
        filename = args[0]
        if not shutil.which("javac"): print(f"{self.RED}Error: 'javac' not found. Is JDK installed?{self.RESET}"); return
        
        print(f"Compiling {filename}...")
        try:
            result = subprocess.run(["javac", filename], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"{self.GREEN}Successfully compiled {filename}{self.RESET}")
                if result.stderr: print(f"{self.YELLOW}Compiler Warnings:\n{result.stderr}{self.RESET}")
            else:
                print(f"{self.RED}Compilation failed:{self.RESET}\n{result.stderr}")
        except KeyboardInterrupt:
            print("\n^C (Compilation cancelled)")

    def cmd_gobuild(self, args):
        """(gobuild) Compiles a .go source file into a binary executable."""
        if not args or not args[0].endswith(".go"):
            print("Usage: gobuild <filename.go> [output_name]"); return
        
        source_file = args[0]
        output_name = args[1] if len(args) > 1 else os.path.splitext(source_file)[0]

        if not os.path.isfile(source_file):
            print(f"{self.RED}Error: Go source file not found: {source_file}{self.RESET}"); return
            
        if not shutil.which("go"):
            print(f"{self.RED}Error: 'go' command not found. Is Go installed?{self.RESET}"); return
        
        print(f"Compiling {source_file} -> {output_name}...")
        command = ["go", "build", "-o", output_name, source_file]
        
        try:
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"{self.GREEN}Successfully compiled executable: {output_name}{self.RESET}")
                if os.name != 'nt':
                    try: os.chmod(output_name, os.stat(output_name).st_mode | 0o111)
                    except OSError as e: print(f"{self.YELLOW}Warning: Could not make output executable: {e}{self.RESET}")
                if result.stderr: print(f"{self.YELLOW}Compiler Messages:\n{result.stderr}{self.RESET}")
            else:
                print(f"{self.RED}Go compilation failed:{self.RESET}\n{result.stderr}")
        except KeyboardInterrupt:
            print("\n^C (Compilation cancelled)")

    def cmd_run(self, args):
        """(run) Executes a script, compiled binary, or Java class."""
        if not args: print("Usage: run <filename> [args...]"); return
        filename, script_args = args[0], args[1:]
        if not os.path.exists(filename): print(f"{self.RED}Error: File not found: {filename}{self.RESET}"); return

        ext = os.path.splitext(filename)[1].lower()
        interpreters = {
            ".py": ["python3", "python"], ".js": ["node"], ".lua": ["lua"],
            ".sh": ["bash", "sh"], ".bash": ["bash", "sh"]
        }
        cmd = None
        
        if ext in interpreters:
            for i in interpreters[ext]:
                if shutil.which(i):
                    cmd = [i, filename] + script_args; break
            if not cmd: print(f"{self.RED}Error: No suitable interpreter found for {filename}.{self.RESET}"); return
        elif ext == ".class":
            if shutil.which("java"):
                class_name = os.path.splitext(os.path.basename(filename))[0]
                class_dir = os.path.dirname(os.path.abspath(filename)) or "."
                cmd = ["java", "-cp", class_dir, class_name] + script_args
            else: print(f"{self.RED}Error: 'java' not found for .class file.{self.RESET}"); return
        elif os.path.isfile(filename) and os.access(filename, os.X_OK):
             cmd = [os.path.abspath(filename)] + script_args
        else:
            print(f"{self.RED}Error: Unsupported or non-executable file type for 'run': {filename}{self.RESET}"); return

        try:
            print(f"Running: {' '.join(cmd)}")
            subprocess.run(cmd, check=True)
        except KeyboardInterrupt:
            print("\n^C")
        except subprocess.CalledProcessError as e: print(f"{self.RED}Execution failed with exit code {e.returncode}.{self.RESET}")
        except Exception as e: print(f"{self.RED}An error occurred while running: {e}{self.RESET}")
    
    def cmd_cowsay(self, args):
        """(cowsay) It's a talking cow."""
        text = " ".join(args) if args else "Moo?"
        max_width = 40
        
        lines = []
        for line in text.split('\n'):
            words = line.split()
            current_line = ""
            for word in words:
                if len(current_line) + len(word) + 1 > max_width:
                    lines.append(current_line); current_line = word
                else: current_line += (" " if current_line else "") + word
            lines.append(current_line)

        box_width = max(len(line) for line in lines) if lines and any(lines) else 0
        
        print(" " + "_" * (box_width + 2))
        for i, line in enumerate(lines):
            padding = " " * (box_width - len(line))
            left, right = ("<", ">") if len(lines) == 1 else ("|", "|")
            print(f" {left} {line}{padding} {right}")
        print(" " + "-" * (box_width + 2))
        
        print("        \   ^__^")
        print("         \  (oo)\_______")
        print("            (__)\       )\/\\")
        print("                ||----w |")
        print("                ||     ||")

    # --- Internal Helper Methods ---
    
    @staticmethod
    def _parse_app_conf_content(content):
        """Parses text content of an app.conf file into a dictionary."""
        conf_data = {}
        for line in content.splitlines():
            line = line.strip().split('#', 1)[0].strip()
            if ":" in line:
                key, value = line.split(":", 1)
                conf_data[key.strip().lower()] = value.strip()
        return conf_data
    
    def _save_repository(self):
        """Saves the current in-memory repository to the repo.txt file."""
        try:
            with open(self.REPO_FILE, "w") as f:
                for name, url in sorted(self.app_repository.items()):
                    f.write(f"{name}\n{url}\n")
        except OSError as e:
            print(f"{self.RED}Error: Could not save repository file: {e}{self.RESET}")

    def _download_file(self, url, filepath):
        """Downloads a file from a URL to a specified path."""
        print(f"Downloading {os.path.basename(url)} -> {os.path.relpath(filepath)}... ", end="", flush=True)
        try:
            parent_dir = os.path.dirname(filepath)
            if parent_dir: os.makedirs(parent_dir, exist_ok=True)
            
            headers = {'User-Agent': f'MyPythonOS Downloader/2.0'}
            with requests.get(url, stream=True, headers=headers, timeout=30, allow_redirects=True) as r:
                r.raise_for_status()
                with open(filepath, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
            print(f"{self.GREEN}Success{self.RESET}")
            return True
        except requests.exceptions.RequestException: print(f"{self.RED}Failed (Network Error){self.RESET}")
        except OSError: print(f"{self.RED}Failed (File System Error){self.RESET}")
        except Exception: print(f"{self.RED}Failed (Unexpected Error){self.RESET}")
        
        if os.path.exists(filepath):
            try: os.remove(filepath)
            except OSError: pass
        return False

    def _get_prompt(self):
        """Constructs and returns the command prompt string."""
        try:
            cwd_abs = os.path.abspath(os.getcwd())
            root_abs = os.path.abspath(self.ROOT_PATH)
            if cwd_abs == root_abs: path_str = "~"
            elif cwd_abs.startswith(root_abs): path_str = f"~/{os.path.relpath(cwd_abs, root_abs).replace(os.sep, '/')}"
            else: path_str = cwd_abs
            return f"{self.GREEN}{self.username}@{self.hostname}{self.RESET}:{self.BLUE}{path_str}{self.RESET} $ "
        except OSError:
            os.chdir(self.ROOT_PATH)
            return f"{self.GREEN}{self.username}@{self.hostname}{self.RESET}:{self.BLUE}~{self.RESET} $ "

    def _run_app(self, command, args):
        """Handles the execution of an installed application."""
        app_info = self.installed_apps[command]
        script_file, app_dir = app_info["script"], app_info["app_dir"]
        original_cwd = os.getcwd()
        
        print(f"Running '{app_info['name']}' (v{app_info['version']}) from '{os.path.relpath(app_dir)}/'...")
        
        ext = os.path.splitext(script_file)[1].lower()
        interpreters = {".py": ["python3", "python"], ".js": ["node"], ".lua": ["lua"], ".sh": ["bash", "sh"]}
        cmd = None
        
        if ext in interpreters:
            for i in interpreters[ext]:
                if shutil.which(i): cmd = [i, script_file] + args; break
            if not cmd: print(f"{self.RED}Error: Interpreter for app not found.{self.RESET}"); return
        elif os.path.isfile(script_file) and os.access(script_file, os.X_OK):
             cmd = [script_file] + args
        else:
            print(f"{self.RED}Error: Cannot run app '{app_info['name']}'. Not executable or unsupported type.{self.RESET}"); return

        try:
            os.chdir(app_dir)
            # This is now wrapped in its own try/except block
            subprocess.run(cmd, check=True)
        except KeyboardInterrupt:
            # Catch Ctrl+C here, print a newline for a clean prompt, and do nothing else.
            print("\n^C")
        except subprocess.CalledProcessError as e:
            print(f"{self.YELLOW}App '{app_info['name']}' exited with non-zero status ({e.returncode}).{self.RESET}")
        except Exception as e:
            print(f"{self.RED}An error occurred while running app '{app_info['name']}': {e}{self.RESET}")
        finally:
            # This ensures we always change back to the original directory
            os.chdir(original_cwd)

    # --- Main Loop & Processing ---

    def process_command_line(self, command_line):
        """Parses and executes a full command string, including pipes."""
        if not command_line: return

        command_sequence = [cmd.strip() for cmd in command_line.split('|') if cmd.strip()]
        for single_command_str in command_sequence:
            try: parts = shlex.split(single_command_str)
            except ValueError as e: print(f"{self.RED}Parse Error: {e}. Check quotes.{self.RESET}"); continue
            
            if not parts: continue
            cmd, args = parts[0].lower(), parts[1:]
            
            if cmd == "exit": self.running = False; break
            
            if hasattr(self, f"cmd_{cmd}"):
                getattr(self, f"cmd_{cmd}")(args)
            elif cmd in self.installed_apps:
                self._run_app(cmd, args)
            else:
                print(f"{self.RED}Command not found: {cmd}{self.RESET}")

    def run(self):
        """The main loop that reads and executes commands interactively."""
        last_command = ""
        while self.running:
            try:
                prompt = self._get_prompt()
                command_line = input(prompt).strip()

                if not command_line:
                    continue
                
                if readline and command_line != last_command:
                    readline.add_history(command_line)
                    last_command = command_line

                self.process_command_line(command_line)
                
            except KeyboardInterrupt:
                # This is the corrected block. It prints ^C for feedback
                # and then does nothing, letting the while loop continue
                # to the next prompt.
                print("\n^C")
                pass
            except EOFError:
                # This remains the same. Ctrl+D will exit the OS.
                print("exit")
                self.running = False
            except Exception:
                print(f"\n{self.RED}--- UNEXPECTED OS ERROR ---{self.RESET}")
                traceback.print_exc()


if __name__ == "__main__":
    try:
        os_instance = MyPythonOS()
        if os_instance.running:
            os_instance.run()
        print(f"{os_instance.ORANGE}MyPythonOS session ended.{os_instance.RESET}")
    except Exception:
        print("\033[91m--- CATASTROPHIC FAILURE ---")
        traceback.print_exc()
        print("MyPythonOS could not start or has crashed unexpectedly.\033[0m")
EOF

echo "--- Python script created. ---"

# --- 3. Make the Python Script Executable ---
chmod +x /usr/local/bin/nullos.py
echo "--- Made script executable. ---"

# --- 4. Create the Startup Service File ---
# This tells Alpine's 'local' service what to run at boot.
echo "--- Creating startup service file... ---"
echo "/usr/local/bin/nullos.py" > /etc/local.d/nullos.start

# --- 5. Make the Startup File Executable ---
chmod +x /etc/local.d/nullos.start
echo "--- Made startup file executable. ---"

# --- 6. Enable the Service to Run on Boot ---
rc-update add local default
echo "--- Service enabled. ---"

# --- Final Message ---
echo ""
echo "========================================================"
echo "          SETUP COMPLETE"
echo "========================================================"
echo "The nullos.py script is now set to run on server start."
echo "Please REBOOT your server from the Pterodactyl panel."
echo "========================================================"
echo ""
