# Null OS

DISCLAIMER:
This is not a real OS. Its a "fake" os, built with python. You have to run this script in an existing OS. I plan to implement it into a minimal Linux kernel for fun tho.

## Description
I made this just for fun, its really cool.
You can make programs with python, lua, js or java and execute them with your cusom made command, or just execute scripts for faster usage in for example developing.

## Commands
  load_user_config: Loads user configuration from user.json.
  create_user_config: Creates user configuration file and prompts for username and hostname.

###  neofetch: Displays system information.
    Usage: neofetch

###  ls: Lists files and directories in the current directory.
    Usage: ls [-l]

###  delf: Deletes a file.
    Usage: delf <filename>

###  deld: Deletes a directory (recursively).
    Usage: deld <directory>

###  cd: Changes the current directory.
    Usage: cd <directory> (or cd to return to root)

###  pwd: Prints the current working directory.
    Usage: pwd

###  mkdir: Creates a new directory.  Creates parent directories as needed.
    Usage: mkdir <directory>

###  touch: Creates a new empty file.
    Usage: touch <filename>

###  clear: Clears the terminal screen.
    Usage: clear

###  edit: Edits a file using nano.
    Usage: edit <filename>

###  download: Downloads a file from a URL.
    Usage: download <url> [directory]

###  run: Runs a code file (Python, Java, Lua, or JavaScript).
    Usage: run <filename>

###  move: Moves a file or directory.
    Usage: move <source> <destination>

###  delpanic:
    Deletes everything except the main python file, and overwrites it with zeroes.
