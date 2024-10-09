#manages sessions and configurations.
import json

SESSION_FILE = ".sessions.json"
KEY_FILE = ".key" 
CONFIG_FILE = "config.json"

config = {}
sessions = {}
availableComponents = {}
files = {}

def getKey():
    try:
        with open(".key", 'r') as file:
            api_key = file.readline().strip()  # Read the first line and strip any extra whitespace/newline
            return api_key
    except FileNotFoundError:
        print(f"Error: Missing {KEY_FILE} file. Please create a {KEY_FILE}  file with your ChatGPT API key in it")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None
    
def get_config():
    global availableComponents 
    global config
    if config:
        return config

    with open(CONFIG_FILE, 'r') as file:
        data = json.load(file)  # Load the JSON content into a Python dictionary
    config = data
    #put components into a dict. 
    for comp in data['components']:
        availableComponents[comp["name"]] = comp    
    return data

def get_components():
    if not availableComponents:
        get_config()
    return availableComponents

def save_sessions():
    try:
        with open(SESSION_FILE, 'w') as file:
            json.dump(sessions, file, indent=4)
        print(f"Session successfully saved to {SESSION_FILE}")
    except Exception as e:
        print(f"An error occurred while saving the session: {e}")

def load_sessions():
    global sessions
    try:
        with open(SESSION_FILE, 'r') as file:
            sessions = json.load(file)
            print(f"Session successfully loaded from {SESSION_FILE}")
            return sessions
    except Exception as e:
        print(f"An error occurred while loading the session: {e}")
        return None
    
def get_assistant(name):
    global sessions
    
    # Check if sessions is None or empty
    if not sessions:
        load_sessions()  # Fetch or initialize sessions
    
    # If sessions is still empty, throw an error
    if not sessions:
        raise ValueError("No sessions available.")
    
    # Check for 'assistants' in sessions
    sess = sessions.get("assistants")
    
    if sess:
        # Iterate through the assistants array to find a match
        for assistant in sess:
            if assistant.get("name") == name:
                return assistant.get("id")
    return None

def set_assistant(assistant):
    global sessions
    assistants = sessions.get("assistants")
    if assistants:
        for asst in assistants:
            if asst.get("name") == assistant.name:
                asst["id"] = assistant.get("id")
                save_sessions()
                return
        assistants.append({"name":assistant.name, "id":assistant.id})
        save_sessions()
    else:
        raise ValueError(f"Couldn't persist Assistant {assistant}")
    

# determines if file exists, is dirty
    # {
    #     "files":[
    #         {"id":"file-S75HFJ6LB94S4B67CXS"
    #         "path":"src/persistence/mongoDBComponent/setup.py"
    #         "dirty":False}
    #     ]
    # }
def get_uploaded_file(path):
    file = files.get(path)
    if file:
        if not file["dirty"]:
            return file["path"]["id"]
    return None


def set_uploaded_file(path, id):
    global files
    file = files.get(path)
    if file:
        file["id"] = id
        file["dirty"] = False
        return
    new_file = {"path":path, "id":id, "dirty":False}   
    files["path"] = new_file
    print(f"setting uploaded file: {path} - {id}")
    print(f"files now: {files}")