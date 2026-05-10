#!/usr/bin/env python3
"""
pycat.py – a simple clone of the Unix 'cat' command.

Usage:
    python3 pycat.py file.txt
    python3 pycat.py file1.txt file2.txt ...
    echo "hello" | python3 pycat.py
"""

import sys

def main():
    # If arguments are provided, treat them as file paths to concatenate
    if len(sys.argv) > 1:
        for filepath in sys.argv[1:]:
            try:
                # Open in binary mode so we can handle any file type (text, images, etc.)
                with open(filepath, 'rb') as f:
                    # Copy file content to stdout in chunks (memory-efficient)
                    while True:
                        chunk = f.read(8192)
                        if not chunk:
                            break
                        sys.stdout.buffer.write(chunk)
            except FileNotFoundError:
                print(f"pycat.py: {filepath}: No such file or directory",
                      file=sys.stderr)
                sys.exit(1)
            except PermissionError:
                print(f"pycat.py: {filepath}: Permission denied",
                      file=sys.stderr)
                sys.exit(1)
            except Exception as e:
                print(f"pycat.py: {filepath}: {e}", file=sys.stderr)
                sys.exit(1)
    else:
        # No filename arguments: read from standard input
        try:
            while True:
                chunk = sys.stdin.buffer.read(8192)
                if not chunk:
                    break
                sys.stdout.buffer.write(chunk)
        except KeyboardInterrupt:
            # Mimic the exit code typically used when a process is interrupted
            sys.exit(130)
        except Exception as e:
            print(f"pycat.py: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == '__main__':
    main()
