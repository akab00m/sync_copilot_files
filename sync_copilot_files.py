import json
import os
from pathlib import Path
from typing import Any

import requests


def get_github_files() -> list[str]:
    """Fetch the list of .instructions.md files from the GitHub repository."""
    url = "https://api.github.com/repos/github/awesome-copilot/contents/instructions"
    response = requests.get(url, timeout=30)

    if response.status_code != 200:
        print(
            f"Error: Could not fetch files from GitHub. Status code: {response.status_code}"
        )
        return []

    files = []
    for item in response.json():
        if item["name"].endswith(".instructions.md"):
            files.append(item["name"])

    return files


def get_local_files(prompts_dir: str) -> list[str]:
    """Get the list of .instructions.md files from the local prompts directory."""
    local_files: list[str] = []
    for file in os.listdir(prompts_dir):
        if file.endswith(".instructions.md"):
            local_files.append(file)

    return local_files


def download_file(file_name: str, download_url: str, save_path: str) -> bool:
    """Download a file from GitHub and save it locally."""
    try:
        response = requests.get(download_url, timeout=30)
        response.raise_for_status()

        with open(save_path, "w", encoding="utf-8") as f:
            f.write(response.text)

        print(f"Downloaded: {file_name}")
        return True
    except Exception as e:
        print(f"Error downloading {file_name}: {str(e)}")
        return False


def load_settings_json(settings_path: str) -> dict[str, Any]:
    """Load the settings.json file."""
    try:
        with open(settings_path, "r", encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)
            return data
    except FileNotFoundError:
        # If file doesn't exist, return an empty dict
        return {}
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {settings_path}")
        return {}


def save_settings_json(settings_path: str, settings_data: dict[str, Any]) -> None:
    """Save data to settings.json file."""
    try:
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(settings_data, f, indent=2, ensure_ascii=False)
        print("Settings.json updated successfully.")
    except Exception as e:
        print(f"Error saving settings.json: {str(e)}")


def update_context_file_names(settings_path: str, prompts_dir: str) -> None:
    """Update the contextFileName array in settings.json with files from prompts directory."""
    settings = load_settings_json(settings_path)

    # Get all .instructions.md files from prompts directory
    local_files = get_local_files(prompts_dir)

    # Convert file names to include the prompts/ prefix
    context_file_names = [f"prompts/{file}" for file in local_files]

    # Update the contextFileName array in settings
    settings["contextFileName"] = context_file_names

    # Save the updated settings
    save_settings_json(settings_path, settings)

    print(
        f"Updated contextFileName in settings.json with {len(context_file_names)} files"
    )


def sync_copilot_files(prompts_dir: str, settings_path: str) -> None:
    """Sync local .instructions.md files with the GitHub repository."""
    # Get files from GitHub
    github_files = set(get_github_files())
    print(
        f"Found {len(github_files)} .instructions.md files on GitHub in instructions directory"
    )

    # Get local files
    local_files = set(get_local_files(prompts_dir))
    print(f"Found {len(local_files)} .instructions.md files locally")

    # Files that exist both locally and on GitHub - these should be updated/replaced
    files_to_update = github_files.intersection(local_files)

    # Files that exist locally but not on GitHub - these will be preserved
    files_to_preserve = local_files - github_files

    print(f"\nFiles with matching names (will be updated): {len(files_to_update)}")
    print(
        f"Local files with non-matching names (will be preserved): {len(files_to_preserve)}"
    )

    # Update existing files with matching names (only files that exist locally)
    for file_name in files_to_update:
        print(f"Updating (replacing): {file_name}")
        # Construct the download URL for the file
        download_url = f"https://raw.githubusercontent.com/github/awesome-copilot/main/instructions/{file_name}"
        save_path = os.path.join(prompts_dir, file_name)
        download_file(file_name, download_url, save_path)

    # Inform about preserved files
    if files_to_preserve:
        print(
            f"\nPreserved files (don't match GitHub files): {', '.join(files_to_preserve)}"
        )

    # Update contextFileName in settings.json to include all files from prompts directory
    update_context_file_names(settings_path, prompts_dir)

    print("\nSync completed!")


if __name__ == "__main__":
    # Define the directory paths - используем %APPDATA% для универсальности
    appdata = os.environ.get("APPDATA")
    if not appdata:
        raise ValueError("APPDATA environment variable is not set")

    prompts_dir = os.path.join(appdata, r"Code - Insiders\User\prompts")
    settings_path = os.path.join(appdata, r"Code - Insiders\User\settings.json")

    # Create directory if it doesn't exist
    Path(prompts_dir).mkdir(parents=True, exist_ok=True)

    sync_copilot_files(prompts_dir, settings_path)
