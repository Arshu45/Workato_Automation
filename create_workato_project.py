

import os
import json
import asyncio
import aiohttp
from dotenv import load_dotenv

WORKATO_API_URL = "https://www.workato.com/api/folders"

def log_error(message):
    print(f"ERROR: {message}")

def print_structure(name, children, level=0):
    print("  " * level + f"- {name}")
    if children:
        for child in children:
            if isinstance(child, dict):
                print_structure(child.get("name"), child.get("children", []), level+1)
            else:
                print("  " * (level+1) + f"- {child}")

async def upsert_project_properties(session, project_id, properties, headers, dry_run, status_report):
    if dry_run:
        status_report.append({"type": "project_properties", "project_id": project_id, "created": False, "properties": properties})
        return None
    url = f"https://www.workato.com/api/properties?project_id={project_id}"
    payload = {"properties": properties}
    async with session.post(url, headers=headers, json=payload) as resp:
        text = await resp.text()
        if resp.status == 200:
            status_report.append({"type": "project_properties", "project_id": project_id, "created": True, "properties": properties})
            return True
        else:
            log_error(f"Failed to upsert project properties for project_id {project_id}: {text}")
            status_report.append({"type": "project_properties", "project_id": project_id, "created": False, "error": text, "properties": properties})
            return False

async def create_recipe(session, recipe, folder_id, headers, dry_run, status_report):
    if dry_run:
        status_report.append({"type": "recipe", "name": recipe.get("name"), "folder_id": folder_id, "created": False})
        return None
    payload = {
        "recipe": {
            "name": recipe.get("name"),
            "code": recipe.get("code"),
            "config": recipe.get("config"),
            "folder_id": str(folder_id),
            "description": recipe.get("description")
        }
    }
    async with session.post("https://www.workato.com/api/recipes", headers=headers, json=payload) as resp:
        text = await resp.text()
        if resp.status == 200:
            data = await resp.json()
            recipe_id = data.get("id")
            status_report.append({"type": "recipe", "name": recipe.get("name"), "folder_id": folder_id, "created": True, "id": recipe_id})
            return recipe_id
        else:
            log_error(f"Failed to create recipe '{recipe.get('name')}' in folder {folder_id}: {text}")
            status_report.append({"type": "recipe", "name": recipe.get("name"), "folder_id": folder_id, "created": False, "error": text})
            return None

async def create_folder(session, name, parent_id, headers, dry_run, status_report, children=None, recipes=None):
    if dry_run:
        status_report.append({"type": "folder", "name": name, "parent_id": parent_id, "created": False})
        return None
    payload = {"name": name}
    if parent_id:
        payload["parent_id"] = parent_id
    async with session.post(WORKATO_API_URL, headers=headers, json=payload) as resp:
        text = await resp.text()
        if resp.status == 200:
            data = await resp.json()
            folder_id = data.get("id")
            status_report.append({"type": "folder", "name": name, "parent_id": parent_id, "created": True, "id": folder_id})
            # Create recipes in this folder
            if recipes:
                for recipe in recipes:
                    await create_recipe(session, recipe, folder_id, headers, dry_run, status_report)
            # Recursively create children
            if children:
                for child in children:
                    if isinstance(child, dict):
                        await create_folder(
                            session,
                            child.get("name"),
                            folder_id,
                            headers,
                            dry_run,
                            status_report,
                            child.get("children", []),
                            child.get("recipes", [])
                        )
                    else:
                        await create_folder(session, child, folder_id, headers, dry_run, status_report)
            return folder_id
        else:
            log_error(f"Failed to create folder '{name}' (parent_id={parent_id}): {text}")
            status_report.append({"type": "folder", "name": name, "parent_id": parent_id, "created": False, "error": text})
            return None

async def main():
    load_dotenv()
    api_token = os.environ.get("WORKATO_API_TOKEN")
    if not api_token:
        api_token = input("Enter your Workato API token: ").strip()
    json_path = input("Enter the path to your folder structure JSON file: ").strip()
    dry_run = input("Dry run mode? (y/n): ").strip().lower() == "y"

    try:
        with open(json_path, "r") as f:
            structure = json.load(f)
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        log_error(f"Error reading JSON file: {e}")
        return

    parent_name = structure.get("parent")
    child_folders = structure.get("children", [])
    if not parent_name or not isinstance(child_folders, list):
        print("Invalid JSON structure. Must contain 'parent' and 'children' list.")
        log_error("Invalid JSON structure. Must contain 'parent' and 'children' list.")
        return

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    print("\nFolder Structure Preview:")
    print_structure(parent_name, child_folders)

    status_report = []
    print("\nCreating folders..." if not dry_run else "\nDry run: No folders will be created.")
    async with aiohttp.ClientSession() as session:
        parent_id = await create_folder(session, parent_name, None, headers, dry_run, status_report, child_folders, structure.get("recipes", []))

        # Upsert project properties if present (after all creation)
        if parent_id and "properties" in structure:
            await upsert_project_properties(session, parent_id, structure["properties"], headers, dry_run, status_report)

    print("\nSummary Report:")
    for entry in status_report:
        if entry["type"] == "folder":
            if entry.get("created"):
                print(f"Created folder: {entry['name']} (ID: {entry.get('id')}, Parent ID: {entry.get('parent_id')})")
            else:
                print(f"Not created folder: {entry['name']} (Parent ID: {entry.get('parent_id')})" + (f" Error: {entry.get('error')}" if entry.get('error') else ""))
        elif entry["type"] == "recipe":
            if entry.get("created"):
                print(f"Created recipe: {entry['name']} (ID: {entry.get('id')}, Folder ID: {entry.get('folder_id')})")
            else:
                print(f"Not created recipe: {entry['name']} (Folder ID: {entry.get('folder_id')})" + (f" Error: {entry.get('error')}" if entry.get('error') else ""))
        elif entry["type"] == "project_properties":
            if entry.get("created"):
                print(f"Upserted project properties for project_id {entry['project_id']}: {entry['properties']}")
            else:
                print(f"Failed to upsert project properties for project_id {entry['project_id']}: {entry.get('error')}")

    print("\nErrors (if any) are shown above.")

if __name__ == "__main__":
    asyncio.run(main())
