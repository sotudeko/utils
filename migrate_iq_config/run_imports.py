import subprocess
import sys
from config import TARGET_URL

# List the scripts in the exact order they need to run for a successful restore
# import_scripts = [
#     "import_baseurl_mail_proxy.py",
#     "import_roles.py",
#     "import_orgs_apps_tags.py",
#     "import_role_mappings.py"
# ]

import_scripts = [
    "import_baseurl_mail_proxy.py",
    "import_roles.py",
    "import_orgs_apps_tags.py",
]

def main():
    print("="*50)
    print(f"STARTING ALL IMPORTS TO TARGET: {TARGET_URL}")
    print("="*50)

    for script in import_scripts:
        print(f"\n>>> RUNNING: {script}")
        
        # Executes the script as a separate system process
        result = subprocess.run([sys.executable, script])
        
        # If a script fails (exit code not 0), we stop to prevent data corruption
        if result.returncode != 0:
            print(f"\n[!] ERROR: {script} failed.")
            print("Stopping the sequence to prevent dependency issues.")
            sys.exit(1)

    print("\n" + "="*50)
    print("ALL IMPORTS COMPLETED SUCCESSFULLY")
    print("="*50)

if __name__ == "__main__":
    main()