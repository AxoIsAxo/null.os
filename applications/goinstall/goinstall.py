#!/usr/bin/env python3
import sys
import platform
import subprocess
import shutil

# --- Helper Functions ---

def run_command(command, sudo=False):
    """
    Runs a command in the shell.
    Prepends 'sudo' if sudo=True and the OS is not Windows.
    Returns True on success, False on failure.
    """
    if sudo and platform.system() != "Windows":
        command.insert(0, "sudo")
        
    print(f"▶️  Running command: {' '.join(command)}")
    try:
        # Use check=True to raise an exception on non-zero exit codes
        subprocess.run(command, check=True, stdout=sys.stdout, stderr=sys.stderr)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"❌ Error running command: {' '.join(command)}")
        print(f"   Reason: {e}")
        return False

def is_go_installed():
    """
    Checks if the 'go' command is available in the system's PATH.
    shutil.which() is a reliable way to check this.
    """
    go_executable = shutil.which("go")
    if go_executable:
        print(f"✅ Go is already installed at: {go_executable}")
        # Optionally, print the version
        run_command(["go", "version"])
        return True
    return False

def install_go():
    """
    Attempts to install Go based on the detected operating system and package manager.
    """
    os_type = platform.system()
    print(f"\nℹ️  Operating System detected: {os_type}")

    if os_type == "Linux":
        return install_go_linux()
    elif os_type == "Darwin": # macOS
        return install_go_macos()
    elif os_type == "Windows":
        return install_go_windows()
    else:
        print(f"❌ Unsupported operating system: {os_type}")
        return False

def install_go_linux():
    """Installer for Linux distributions."""
    print("🐧 Attempting to install Go for Linux...")
    
    # Check for APT (Debian, Ubuntu)
    if shutil.which("apt"):
        print("   Found 'apt' package manager.")
        if not run_command(["apt", "update"], sudo=True):
            return False
        return run_command(["apt", "install", "-y", "golang-go"], sudo=True)
        
    # Check for DNF/YUM (Fedora, CentOS, RHEL)
    elif shutil.which("dnf"):
        print("   Found 'dnf' package manager.")
        return run_command(["dnf", "install", "-y", "golang"], sudo=True)
    elif shutil.which("yum"):
        print("   Found 'yum' package manager.")
        return run_command(["yum", "install", "-y", "golang"], sudo=True)
        
    # Check for Pacman (Arch Linux)
    elif shutil.which("pacman"):
        print("   Found 'pacman' package manager.")
        return run_command(["pacman", "-Syu", "--noconfirm", "go"], sudo=True)
        
    else:
        print("❌ Could not find a supported package manager (apt, dnf, yum, pacman).")
        print("   Please install Go manually from https://go.dev/doc/install")
        return False

def install_go_macos():
    """Installer for macOS."""
    print("🍎 Attempting to install Go for macOS...")
    if not shutil.which("brew"):
        print("❌ Homebrew ('brew') is not installed.")
        print("   Please install Homebrew first by following the instructions at https://brew.sh/")
        return False
    
    print("   Found 'brew' package manager.")
    if not run_command(["brew", "update"]):
        return False
    return run_command(["brew", "install", "go"])

def install_go_windows():
    """Installer for Windows."""
    print("🪟 Attempting to install Go for Windows...")
    if not shutil.which("choco"):
        print("❌ Chocolatey ('choco') is not installed.")
        print("   Chocolatey is the recommended way to install Go from this script.")
        print("   Please install it first from https://chocolatey.org/install")
        print("\nAlternatively, install Go manually from https://go.dev/doc/install")
        return False
        
    print("   Found 'choco' package manager.")
    # On Windows, commands are typically run with admin rights already if choco is used
    return run_command(["choco", "install", "golang", "-y"])

# --- Main Execution ---

def main():
    """
    Main function to check for and install Go.
    """
    print("--- Go (Golang) Installation Checker ---")
    
    if is_go_installed():
        sys.exit(0) # Exit successfully

    print("\n गो Go installation not found. Attempting to install...")
    
    # Attempt the installation
    install_success = install_go()
    
    if not install_success:
        print("\n❌ Go installation failed. Please review the error messages above.")
        print("   You may need to run this script with administrative privileges (e.g., using 'sudo').")
        print("   For manual installation, visit: https://go.dev/doc/install")
        sys.exit(1)

    print("\n✨ Installation command completed. Verifying installation...")
    
    # Verify installation after the attempt
    if is_go_installed():
        print("\n✅ Successfully installed and verified Go.")
        print("   You may need to open a new terminal session for the 'go' command to be available.")
        sys.exit(0)
    else:
        print("\n❌ Verification failed. The 'go' command is still not available.")
        print("   The installation may have completed, but the command is not in your system's PATH.")
        print("   Please open a new terminal or restart your system. If the issue persists, check your PATH environment variable.")
        sys.exit(1)

if __name__ == "__main__":
    main()
