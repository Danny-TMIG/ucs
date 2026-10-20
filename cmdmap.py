"""Command mapping module for orchestration."""
COMMAND_MAP = {
    "stage": "orchestrate.py stage",
    "release": "release.py go",
    "test": "pytest",
}

def get_command(name):
    return COMMAND_MAP.get(name)

if __name__ == "__main__":
    print("cmdmap.py OK")
