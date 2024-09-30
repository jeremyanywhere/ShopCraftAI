import json
import os
import sys
from chatgptAPIUtils import createAssistants

config = {}
availableComponents = {}
currentComponent = {}
rootDirectory = {}
promptMode = False

def read_config_file(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)  # Load the JSON content into a Python dictionary
    #put components into a dict. 
    for comp in data['components']:
        availableComponents[comp["name"]] = comp
    return data

def verify(msg: str) -> bool:
    # Print the message followed by "(yes/no)"
    user_input = input(f"{msg} (yes/no): ").strip().lower()
    
    # Return True only if the user types 'yes'
    return user_input == "yes"

# Define the available commands as functions
def list(param=None):
    if param == None or param =='commands':
        for command in available_commands.keys():
            print(f"- {command}")
    elif param=='components':
        for component in availableComponents:
            print (f"Component: {availableComponents[component]['name']} - (type: {availableComponents[component]['type']} )")
    else:
        print(f"Param <{param}> for command 'list'  not known.") 

def clean(param=None):
    if param == "all":
        verify("Are you sure,")
    else:
        print("usage: clean <component> | all")
        
def create(param=None):
        # Ensure the base directory exists
    if not os.path.exists(config['source']):
        os.makedirs(config['source'])
    # Iterate through each component in the config
    for component in config.get('components', []):
        subdir_name = component.get('workdir')
        if subdir_name:
            subdir_path = os.path.join(config['source'], subdir_name)
            
            # Check if the subdirectory already exists
            if os.path.exists(subdir_path):
                print(f"Directory '{subdir_name}' already exists.")
            else:
                # Create the subdirectory
                os.makedirs(subdir_path)
                print(f"Created directory '{subdir_name}'.")
        else:
            print("No 'workdir' key found for a component.")

        print("Created src structure and run startup prompts ")

def select(param=None):
    global currentComponent
    if param:
        value = availableComponents.get(param, '')
        if value:
            currentComponent = value
            promptMode == True
            print("Entering Prompt Mode:")
            print(f"Component set to '{currentComponent['name']}")
        else:
            print(f"Component '{param}' not found.")
    else:
        print("usage: greet <name>")

def exit_program(param=None):
    global currentComponent
    global promptMode

    if not promptMode:
        print("Bye.")
        sys.exit()
    promptMode = False
    print("Closing Prompt Mode.")
    currentComponent = {}

# Create a dictionary to map command names to functions and whether they accept parameters
available_commands = {
    '.create': create,
    '.help': list,
    '.list': list,
    '.clean': clean,
    '.select': select,
    '.exit': exit_program
}

def go():
    list()
    print ("ShopCraftAI CLI.")
    while True:
        # Accept user input and split it into command and parameter (if provided)
        compName = ""
        if len(currentComponent)>0:
            compName = currentComponent["name"] 
            
        user_input = input(f"{compName} >: ").strip().split()
        
        if not user_input:
            print("No command entered. Try again.")
            continue
        
        command = user_input[0].lower()  # The command is the first word
        param = user_input[1] if len(user_input) > 1 else None  # The parameter is the second word, if available
        # Check if the command exists in the available commands
        if command in available_commands:
                available_commands[command](param)
        else:
            # Output error for unknown command
            if promptMode:
                print(f"will send prompt to chatGPT Assistant");
            else:
                print(f"Error: '{command}' is not a recognized command. Type 'list' to see available commands.")

# Run the command loop
def main():
    global config 
    config = read_config_file("config.json")
    print(f"Config is {config}")
    print(availableComponents)
    go()

main()






# Print the resulting dictionary
