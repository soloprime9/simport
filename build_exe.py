import os
import sys
import subprocess
import shutil

try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def build_windows_exe():
    print("=" * 60)
    print("[*] BUILDING STANDALONE WINDOWS EXECUTABLE (.EXE)")
    print("=" * 60)

    # Output executable name
    exe_name = "SIM_MNP_Portal"

    # PyInstaller arguments
    # On Windows, PyInstaller --add-data uses ';' separator (source;dest)
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", exe_name,
        "--onefile",
        "--clean",
        "--add-data", f"static{os.pathsep}static",
        "--add-data", f"portal_config.json{os.pathsep}.",
        "--hidden-import", "jinja2",
        "--hidden-import", "werkzeug",
        "--hidden-import", "requests",
        "app.py"
    ]

    print(f"Running command: {' '.join(cmd)}\n")
    result = subprocess.run(cmd, cwd=BASE_DIR)

    if result.returncode == 0:
        exe_path = os.path.join(BASE_DIR, "dist", f"{exe_name}.exe")
        print("\n" + "=" * 60)
        print("[SUCCESS] EXECUTABLE CREATED SUCCESSFULLY!")
        print(f"Location: {exe_path}")
        if os.path.exists(exe_path):
            print(f"Size: {os.path.getsize(exe_path) / (1024*1024):.2f} MB")
        print("=" * 60)
        print("\nHow to use:")
        print("1. Double click 'SIM_MNP_Portal.exe' on any Windows machine.")
        print("2. It will automatically start the server and open http://localhost:5050 in your default browser!")
    else:
        print("\n[ERROR] Build failed with return code:", result.returncode)

if __name__ == "__main__":
    build_windows_exe()
