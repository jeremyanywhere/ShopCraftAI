#manages sessions and configurations.
import json
import logger

SESSION_FILE = ".sessions.json"
KEY_FILE = ".key" 
CONFIG_FILE = "config.json"

config = {}
sessions = {}
availableComponents = {}
logging = logger.logger


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
        logging.debug(f"Session successfully saved to {SESSION_FILE}")
    except Exception as e:
        print(f"Error! An error occurred while saving the session: {e}")

def load_sessions():
    global sessions
    try:
        with open(SESSION_FILE, 'r') as file:
            sessions = json.load(file)
            logging.debug(f"Session successfully loaded from {SESSION_FILE}")
            return sessions
    except Exception as e:
        print(f"Error! An error occurred while loading the session: {e}")
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
    if not sessions:
        load_sessions()
    files = sessions.get("files")
    if files == None:
        return None
    for f in files.values():
        logging.debug(f"f is {f},  of type {type(f)}")
        if f["path"] == path and not f["dirty"]:
            return f["id"]
    return None

def set_uploaded_file_dirty(path):
    global sessions
    if not sessions:
        load_sessions()
    #we have updated the local copy of the file, the file needs to be updated next time.
    files = sessions.get("files")
    if not files:
        print(f"Error. Unexpected file synch map not found.")
        return
    for f in files.values():
        if f["path"] == path:
            f["dirty"] = True
    save_sessions()

#files which have been edited since last upload so they are dirty or invalidated
def get_dirty_uploaded_file_ids():
    global sessions
    if not sessions:
        load_sessions()
    dirty_files = []
    files = sessions.get("files")
    if not files:
        print(f"Error. Unexpected file synch map not found.")
        return []
    for f in files.values():
        if f["dirty"] == True:
            dirty_files.append(f["id"])
    return dirty_files

def set_uploaded_file(path, id):
    #if we find the existing path, for a different ID, 
    #then we must make it dirty. 
    global sessions
    files = sessions.get("files")
    if not files:
        files = {}
    new_file = {"path":path, "id":id, "dirty": False}   
    files[id] = new_file
    logging.debug(f"setting uploaded file: {path} - {id}")
    logging.debug(f"files now: {files}")
    sessions["files"] = files
    save_sessions()

def remove_dirty_uploaded_file_ids():
    #if we find the existing path, for a different ID, 
    #then we must make it dirty. 
    global sessions
    files = sessions.get("files")
    if not files:
        return
    files_to_remove = []
    for f in files.values():
        if f["dirty"] == True:
            files_to_remove.append(f["id"])
    for ftr in files_to_remove:
        del files[ftr]
    save_sessions()