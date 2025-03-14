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

# ANSI escape codes for colors
RED = '\033[91m'
ORANGE = '\033[38;5;208m'  # A good orange color
YELLOW = '\033[93m'
GREEN = '\033[92m'
BLUE = '\033[94m'
PURPLE = '\033[95m'
RESET = '\033[0m'

ROOT_DIR_NAME = "root"  # Customize this if you want a different root name
ROOT_PATH = os.path.abspath("./")  # Define the root path globally
USER_CONFIG_FILE = os.path.join(ROOT_PATH, "user.json")
APPLICATIONS_DIR = os.path.join(ROOT_PATH, "applications")  # Directory for applications
INSTALLED_APPS = {}  # Dictionary to store installed applications info
MAIN_SCRIPT = os.path.basename(__file__) # Name of current script

def load_user_config():
    """Loads user configuration from user.json."""
    if os.path.exists(USER_CONFIG_FILE):
        try:
            with open(USER_CONFIG_FILE, "r") as f:
                config = json.load(f)
                return config.get("username", "user"), config.get("hostname", "hostname")
        except json.JSONDecodeError:
            print("Error: Could not decode user.json.  Using defaults.")
            return "user", "hostname"
    else:
        return None, None


def create_user_config():
    """Creates user configuration file and prompts for username and hostname."""
    username = input("Enter username: ").strip()
    hostname = input("Enter hostname: ").strip()

    config = {"username": username, "hostname": hostname}

    try:
        with open(USER_CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
        print("User configuration saved to user.json")
        return username, hostname
    except OSError as e:
        print(f"Error: Could not create user.json: {e}")
        return "user", "hostname"  # Provide defaults in case of error

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
                                                                                                                                                         
                                                                                                                                                      
                                                                                                                                                         
{RESET}"""  # Add the reset AFTER the art


def neofetch():
    """Displays system information.
       Usage: neofetch"""
    print(NEOFETCH_ART)  # Print the ASCII art first

    os_name = "MyPythonOS"
    kernel = platform.system()
    architecture = platform.machine()
    python_version = platform.python_version()
    cwd = os.getcwd()
    num_files = len([f for f in os.listdir(cwd) if os.path.isfile(f)])
    num_dirs = len([d for d in os.listdir(cwd) if os.path.isdir(d)])

    print(f"""
        OS: {os_name}
        Kernel: {kernel}
        Architecture: {architecture}
        Python: {python_version}
        Files: {num_files}
        Directories: {num_dirs}
        CWD: {cwd}
        """)


def ls(args=None):
    """Lists files and directories in the current directory.
       Usage: ls [-l]"""
    try:
        if args:
            # Handle arguments, e.g., "ls -l" (simple example, doesn't implement full ls options)
            if args[0] == "-l":
                # Print detailed listing (very basic)
                for item in os.listdir(os.getcwd()):
                    file_path = os.path.join(os.getcwd(), item)
                    if os.path.isfile(file_path):
                        file_type = "File"
                    elif os.path.isdir(file_path):
                        file_type = "Directory"
                    else:
                        file_type = "Unknown"
                    print(f"{file_type:<10} {item}")
            else:
                print("Invalid argument for ls.")
                return

        else:
            # Basic listing
            for item in os.listdir(os.getcwd()):
                print(item)
    except OSError as e:
        print(f"Error: {e}")


def delf(filename):
    """Deletes a file.
       Usage: delf <filename>"""
    try:
        os.remove(filename)
        print(f"Deleted: {filename}")
    except FileNotFoundError:
        print(f"Error: File not found: {filename}")
    except OSError as e:
        print(f"Error: {e}")


def deld(dirname):
    """Deletes a directory (recursively).
       Usage: deld <directory>"""
    try:
        shutil.rmtree(dirname)  # Be very careful with this command!
        print(f"Deleted directory: {dirname}")
    except FileNotFoundError:
        print(f"Error: Directory not found: {dirname}")
    except OSError as e:
        print(f"Error: {e}")


def cd(directory=None):
    """Changes the current directory.
       Usage: cd <directory> (or cd to return to root)"""
    if not directory:
        # "cd" with no arguments returns to the root directory.
        try:
            os.chdir(ROOT_PATH)
        except OSError as e:
            print(f"Error: Could not change directory to root: {e}")
    else:
        try:
            os.chdir(directory)  # Change the current working directory
        except FileNotFoundError:
            print(f"Error: Directory not found: {directory}")
        except NotADirectoryError:
            print(f"Error: Not a directory: {directory}")
        except OSError as e:
            print(f"Error: {e}")


def pwd():
    """Prints the current working directory.
       Usage: pwd"""
    print(os.getcwd())


def mkdir(dirname):
    """Creates a new directory.  Creates parent directories as needed.
       Usage: mkdir <directory>"""
    try:
        os.makedirs(dirname, exist_ok=True)  # Creates parent directories if they don't exist
        print(f"Created directory: {dirname}")
    except OSError as e:
        print(f"Error: Could not create directory: {e}")


def touch(filename):
    """Creates a new empty file.
       Usage: touch <filename>"""
    try:
        with open(filename, 'w'):  # Creates an empty file
            pass
        print(f"Created file: {filename}")
    except OSError as e:
        print(f"Error: {e}")


def help():
    """Displays available commands and their usage."""
    print("Available commands:")
    for name, obj in globals().items():
        if callable(obj) and obj.__module__ == __name__ and name != "help":  # check for functions in current module
            docstring = inspect.getdoc(obj)
            if docstring:
                print(f"  {name}: {docstring.splitlines()[0]}")
                for line in docstring.splitlines()[1:]:  # Print additional lines of docstring
                    print(f"    {line}")  # Indent subsequent lines
            else:
                print(f"  {name}: (No help available)")


def clear():
    """Clears the terminal screen.
       Usage: clear"""
    os.system('cls' if os.name == 'nt' else 'clear')  # Cross-platform clear


def edit(filename):
    """Edits a file using nano.
       Usage: edit <filename>"""
    try:
        # Attempt to use nano
        subprocess.run(["nano", filename], check=True)  # Raises an exception if nano fails

        # After successful editing, reload applications
        if filename.endswith(".conf"):
            #Clear apps
            INSTALLED_APPS.clear()

            load_applications()

            return # Return so code is not called unnessecaryly

    except FileNotFoundError as e:
        print(f"Error: Nano not found: {e}")
    except subprocess.CalledProcessError as e:
        print(f"Error: Nano exited with an error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def download(url, destination=None):
    """Downloads a file from a URL.
       Usage: download <url> [directory]"""
    try:
        response = requests.get(url, stream=True, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

        # Extract filename from URL
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)

        if destination:
            # Check if the destination directory exists
            if not os.path.isdir(destination):
                print(f"Error: Directory not found: {destination}")
                return

            filepath = os.path.join(destination, filename)
        else:
            filepath = filename  # Save in the current directory

        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"Downloaded: {url} to {filepath}")

    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url}: {e}")
    except OSError as e:
        print(f"Error saving file: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")  # Catch all other potential errors.

def run(filename):
    """Runs a code file (Python, Java, Lua, or JavaScript).
    Usage: run <filename>"""
    try:
        # Try 'python3' first, then fallback to 'python'
        try:
            subprocess.run(["python3", filename], check=True)
        except FileNotFoundError:
            subprocess.run(["python", filename], check=True)
        except Exception as e:
            print(f"Error: Execution failed: {e}")

    except FileNotFoundError as e:
        print(f"Error: Interpreter not found: {e}")
        print("Please make sure that Python, Java, Lua, and Node.js are installed and in your system's PATH.")
    except subprocess.CalledProcessError as e:
        print(f"Error: Execution failed: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def move(source, destination):
    """Moves a file or directory.
       Usage: move <source> <destination>"""
    try:
        shutil.move(source, destination)
        print(f"Moved: {source} to {destination}")
    except FileNotFoundError:
        print(f"Error: Source file/directory not found: {source}")
    except OSError as e:
        print(f"Error: Could not move {source} to {destination}: {e}")

def setup_app(app_dir):
    """Sets up an application from a directory."""
    conf_file = os.path.join(app_dir, os.path.basename(app_dir) + ".conf")
    script_file = None

    # Find script file
    for file in os.listdir(app_dir):
        if file.endswith((".py", ".java", ".lua", ".js")):
            script_file = os.path.join(app_dir, file)
            break

    if not os.path.exists(conf_file) or not script_file:
        print(f"Error: Invalid app structure in {app_dir}. Missing conf file or script.")
        return

    try:
        with open(conf_file, "r") as f:
            conf_data = {}
            for line in f:
                if ":" in line:
                    key, value = line.strip().split(":", 1)
                    conf_data[key.strip()] = value.strip()

            name = conf_data.get("name")
            command = conf_data.get("command")
            version = conf_data.get("version")

            if not name or not command or not version:
                print(f"Error: Invalid conf file in {app_dir}. Missing 'name', 'command', or 'version'.")
                return

            if command in globals() and callable(globals()[command]):
                print(f"Error: Command '{command}' already exists as a base command.  Cannot set up app in {app_dir}.")
                return

            if command in INSTALLED_APPS:
                print(f"Error: Command '{command}' already exists for another app.  Cannot set up app in {app_dir}.")
                return

            INSTALLED_APPS[command] = {
                "name": name,
                "script": script_file,
                "version": version,
                "app_dir": app_dir
            }

            print(f"Successfully set up app '{name}' (command: {command}) from {app_dir}")

    except Exception as e:
        print(f"Error setting up app from {app_dir}: {e}")

def load_applications():
    """Loads applications from the applications directory."""
    if not os.path.exists(APPLICATIONS_DIR):
        try:
            os.mkdir(APPLICATIONS_DIR)
            print("Created 'applications' directory.")
        except OSError as e:
            print(f"Error: Could not create 'applications' directory: {e}")
            return

    for item in os.listdir(APPLICATIONS_DIR):
        item_path = os.path.join(APPLICATIONS_DIR, item)
        if os.path.isdir(item_path):
            setup_app(item_path)

def app(command):
    """Runs an installed application."""
    if command not in INSTALLED_APPS:
        print(f"Error: Application '{command}' not found.")
        return

    app_info = INSTALLED_APPS[command]
    script_file = app_info["script"]

    try:
        # Updated here too, try python3 and fallback
        try:
             subprocess.run(["python3", script_file], check=True)
        except FileNotFoundError:
            subprocess.run(["python", script_file], check=True)
        except Exception as e:
            print(f"Error: Execution failed: {e}")

    except FileNotFoundError as e:
        print(f"Error: Interpreter not found: {e}")
    except subprocess.CalledProcessError as e:
        print(f"Error: Execution failed: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def get_prompt(username, hostname):
    """Generates the custom prompt."""
    cwd = os.getcwd()

    if cwd == ROOT_PATH:
        return f"{username}@{hostname} {ROOT_DIR_NAME} $ "
    else:
        relative_path = os.path.relpath(cwd, ROOT_PATH)
        return f"{username}@{hostname}:~/{relative_path} $ "

def delpanic():
    """Deletes everything except the main python file, and overwrites it with zeroes (or the best way to make it unrecoverable). Do it so you have to type in 3 random sentences to confirm."""

    #Generate 3 random sentences:
    sentences = [
        "The quick brown fox jumps over the lazy dog.",
        "Never gonna give you up, never gonna let you down.",
        "All your base are belong to us.",
        "A penny saved is a penny earned.",
        "Early to bed, early to rise, makes a man healthy, wealthy and wise."
    ]

    chosen_sentences = random.sample(sentences, 3)
    print("Please type in the following sentences to confirm:")
    for sentence in chosen_sentences:
        print(sentence)

    for i in range(3):
        user_input = input(f"Sentence {i + 1}: ")
        if user_input != chosen_sentences[i]:
            print("Confirmation failed. Aborting delpanic.")
            return

    print("Confirmation successful. Initiating DELPANIC...")

    # Get the name of the current script file
    current_script = os.path.basename(__file__)

    for item in os.listdir(ROOT_PATH):
        item_path = os.path.join(ROOT_PATH, item)
        if item != current_script:
            try:
                if os.path.isfile(item_path):
                    # Overwrite with zeroes
                    file_size = os.path.getsize(item_path)
                    with open(item_path, "wb") as f:
                        f.write(b"\0" * file_size)

                    os.remove(item_path)
                    print(f"Deleted file: {item}")
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                    print(f"Deleted directory: {item}")
            except Exception as e:
                print(f"Error deleting {item}: {e}")

    print("DELPANIC complete.")

def main():
    """Main loop of the simulated terminal."""
    global ROOT_PATH  # make sure that ROOT_PATH is modified globally
    # Load applications from the applications directory
    load_applications()
    # Load user configuration
    username, hostname = load_user_config()

    if not username or not hostname:
        username, hostname = create_user_config()  # Create if it doesnt exist

    while True:
        prompt = get_prompt(username, hostname)  # Get the dynamic prompt
        command = input(prompt).strip()

        if command == "exit":
            break

        parts = command.split()
        cmd = parts[0]

        #THIS IS THE FIX:

        if cmd == "neofetch":
            neofetch()
        elif cmd == "ls":
            ls(parts[1:]) if len(parts) > 1 else ls()
        elif cmd == "delf":
            if len(parts) > 1:
                delf(parts[1])
            else:
                print("Usage: delf <filename>")
        elif cmd == "deld":
            if len(parts) > 1:
                deld(parts[1])
            else:
                print("Usage: deld <directory>")
        elif cmd == "cd":
            if len(parts) > 1:
                cd(parts[1])
            else:
                cd()
        elif cmd == "pwd":
            pwd()
        elif cmd == "mkdir":
            if len(parts) > 1:
                mkdir(parts[1])
            else:
                print("Usage: mkdir <directory>")
        elif cmd == "touch":
            if len(parts) > 1:
                touch(parts[1])
            else:
                print("Usage: touch <filename>")
        elif cmd == "help":
            help()
        elif cmd == "clear":
            clear()
        elif cmd == "edit":
            if len(parts) > 1:
                edit(parts[1])
            else:
                print("Usage: edit <filename>")
        elif cmd == "download":
             if len(parts) > 1:
                url = parts[1]
                destination = parts[2] if len(parts) > 2 else None
                download(url, destination)
             else:
                print("Usage: download <url> [directory]")
        elif cmd == "run":
            if len(parts) > 1:
                run(parts[1])
            else:
                print("Usage: run <filename>")
        elif cmd == "delpanic":
            delpanic()
        elif cmd == "move":
            if len(parts) == 3:
                move(parts[1], parts[2])
            else:
                print("Usage: move <source> <destination>")
        elif cmd in INSTALLED_APPS:
            app(cmd) # Run installed app

        else:  # if its not empty
            print(f"Command not found: {cmd}")


if __name__ == "__main__":
    # Load applications from the applications directory

    main()