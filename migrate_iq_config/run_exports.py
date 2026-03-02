import subprocess
import sys
from config import SOURCE_URL

# List the scripts in the exact order they need to run
export_scripts = [
    "export_baseurl_mail_proxy.py",
    "export_roles.py",
    "export_orgs_apps_tags.py",
    "export_role_mappings.py"
]

def main():
    print("="*50)
    print(f"STARTING ALL EXPORTS FROM: {SOURCE_URL}")
    print("="*50)

    for script in export_scripts:
        print(f"\n>>> RUNNING: {script}")
        
        # Executes the script as a separate process
        result = subprocess.run([sys.executable, script])
        
        if result.returncode != 0:
            print(f"[!] ERROR: {script} failed. Stopping sequence.")
            sys.exit(1)

    print("\n" + "="*50)
    print("ALL EXPORTS COMPLETED SUCCESSFULLY")
    print("="*50)

if __name__ == "__main__":
    main()