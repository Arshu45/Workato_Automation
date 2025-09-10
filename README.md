# Workato Automation

This project automates the creation of Workato projects, folders, and recipes using Workato's public APIs.

## Prerequisites
- Python 3.8+
- [pip](https://pip.pypa.io/en/stable/)
- Workato API token

## Setup
1. **Clone the repository or download the script.**
2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
3. **Create a `.env` file in the project root:**
   ```env
   WORKATO_API_TOKEN=your_workato_api_token_here
   ```
4. **Prepare your folder structure JSON file.**
   Example:
   ```json
   {
     "parent": "Arsh Test",
     "children": [
       {
         "name": "Contact Sync",
         "recipes": [
           {"name": "Contact Sync", "code": "{}", "config": "[]", "description": "Contact sync recipe"}
         ]
       },
       {
         "name": "Pom Sync",
         "recipes": [
           {"name": "Aws Lambda", "code": "{}", "config": "[]", "description": "AWS Lambda recipe"},
           {"name": "Pom Sync", "code": "{}", "config": "[]", "description": "Pom sync recipe"}
         ]
       },
       {
         "name": "Activity Sync",
         "recipes": [
           {"name": "Evict Activities", "code": "{}", "config": "[]", "description": "Evict activities recipe"},
           {"name": "Buffer Activities", "code": "{}", "config": "[]", "description": "Buffer activities recipe"}
         ]
       }
     ]
   }
   ```

## Running the Script
1. **Activate your Python environment (if using one):**
   ```sh
   # On Windows
   .\env\Scripts\activate
   # On Mac/Linux
   source env/bin/activate
   ```
2. **Run the script:**
   ```sh
   python create_workato_project.py
   ```
3. **Follow the prompts:**
   - Enter the path to your folder structure JSON file.
   - Choose dry run mode (y/n).

## Notes
- The script will print a summary of created folders and recipes.
- Dry run mode allows you to preview actions without making API calls.
- Make sure your API token is valid and has the necessary permissions.

## Troubleshooting
- If you see import errors for `aiohttp` or `python-dotenv`, install them:
  ```sh
  pip install aiohttp python-dotenv
  ```
- If you get API errors, check your token and JSON structure.

## License
MIT
