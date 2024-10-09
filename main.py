import json
import os
import sys
import chatgptAPIUtils
import configurations

config = {}
assistants = {}
rootDirectory = {}
promptMode = False #deprecated



def verify(msg: str) -> bool:
    # Print the message followed by "(yes/no)"
    user_input = input(f"{msg} (yes/no): ").strip().lower()
    
    # Return True only if the user types 'yes'
    return user_input == "yes"



def get_component_directory(component):
    workdir = component.get("workdir")
    source_dir = config.get("source")
    
    if workdir and source_dir:
        # Combine source_dir and workdir to form the full path
        full_path = os.path.join(source_dir, workdir)
        
        if os.path.exists(full_path) and os.path.isdir(full_path):
            return full_path
        else:
            print(f"Error: The directory '{full_path}' does not exist or is not accessible.")
    else:
        print(f"Error: Could not find 'workdir' or 'source' in the configuration.")
    return None
# Define the available commands as functions
def list(param=None):
    global promptMode  # Access the global variable promptMode
    global currentComponent  # Access the global variable currentComponent
    global config  # Access the global config dict
    
    # Check if promptMode is True
    if promptMode:
        workdir = currentComponent.get("workdir")
        source_dir = config.get("source")
        
        if workdir and source_dir:
            # Combine source_dir and workdir to form the full path
            full_path = os.path.join(source_dir, workdir)
            
            if os.path.exists(full_path) and os.path.isdir(full_path):
                # List files in the full directory path
                print(f"Listing files in {full_path}:")
                for file_name in os.listdir(full_path):
                    print(file_name)
            else:
                print(f"The directory '{full_path}' does not exist or is not accessible.")
        else:
            print(f"Error: Could not find 'workdir' or 'source' in the configuration.")
    
    else:
        # Original behavior if promptMode is False
        if param == None or param == 'commands':
            for command in available_commands.keys():
                print(f"- {command}")
        elif param == 'components':
            for component in configurations.get_components():
                print(f"Component: {configurations.get_components()[component]['name']} - (type: {configurations.get_components()[component]['type']} )")
        else:
            print(f"Param <{param}> for command 'list' not known.")

def clean(param=None):
    if param == "all":
        verify("Are you sure,")
    else:
        print("usage: clean <component> | all")
        
def set_up(param=None):
    global assistants
    global config
    
    # If param is None, return the usage string
    if param is None:
        return "usage: setup <name | all>"
    
    # Ensure the base directory exists
    if not os.path.exists(config['source']):
        os.makedirs(config['source'])
    
    # If param is 'all', loop through all components
    if param == "all":
        for component in config.get('components', []):
            subdir_name = component.get('workdir')
            if subdir_name:
                subdir_path = os.path.join(config['source'], subdir_name)
                
                if os.path.exists(subdir_path):
                    print(f"Directory '{subdir_name}' already exists.")
                else:
                    os.makedirs(subdir_path)
                    print(f"Created directory '{subdir_name}'.")
                
                # Pass the current component to chatgptAPIUtils.run_set_up
                chatgptAPIUtils.set_up_run(component, config)
            else:
                print("No 'workdir' key found for a component.")
                return
    else:
        # If param is a string representing a component name
        component = next((comp for comp in config.get('components', []) if comp.get('name') == param), None)
        
        if component:
            # Pass the found component to chatgptAPIUtils.run_set_up
            subdir_name = component.get('workdir')
            if subdir_name:
                subdir_path = os.path.join(config['source'], subdir_name)
                
                if os.path.exists(subdir_path):
                    print(f"Directory '{subdir_name}' already exists.")
                else:
                    os.makedirs(subdir_path)
                    print(f"Created directory '{subdir_name}'.")
                
                # Call the setup function for this component
                chatgptAPIUtils.set_up_run(component, config)
        else:
            print(f"Component with name '{param}' not found.")

def edit(param=None):
    global config
    component = {}
    if param:
        component = configurations.get_components().get(param, '')
        if component:
            print(f"Entering Edit Mode for '{component.get('name')}'")
        else:
            print(f"Component '{param}' not found.")
            return
    else:
        print("usage: edit <name>")
        return
    while True:
        print ("Type your prompt, use '/' to preceed commands '/view', or '/exit' or '/with <filename>' to only attach a specific file")
        component_path = get_component_directory(component)
        user_input = input(f"{component.get('name')} > ")
        if not user_input:
            continue
        if not user_input.startswith("/") and not len(user_input) > 7:
            print(f"Prompt too short! Did you mean to type a command? Preceed with / '")
            continue
        if user_input.startswith("/exit"):
            print(f"Exiting Edit Mode.'")
            return
        if user_input.startswith("/view"):
            print(f"Listing files in component directory {component_path}:")
            for file_name in os.listdir(component_path):
                 print(f"    {file_name}")
            print("\n") 
            continue   
        if user_input.startswith("/with"):
            # check file exists, then upload that file only before executing prompt
            without_with = user_input.split("/with ", 1)[1]
            with_file = without_with.split()[0]
            prompt = without_with[len(with_file):].strip()
            chatgptAPIUtils.execute_prompt(component, config, prompt, with_file)
            continue
        chatgptAPIUtils.execute_prompt(component, config, user_input)

def init(param=None):
    global currentComponent
    global promptMode
    global config

    if param:
        comp = configurations.get_components().get(param, '')
        if comp:
            print(f"Starting Component '{comp.get('name')}'")
            chatgptAPIUtils.run_set_up(comp, config)
        else:
            print(f"Component '{param}' not found.")
    else:
        print("usage: init <name>")

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
    'setup': set_up,
    'help': list,
    'list': list,
    'clean': clean,
    'edit': edit,
    'init': init,
    'exit': exit_program
}
def prompt(component):
    return

def go():
    list()
    print ("ShopCraftAI CLI.")
    while True:
        # Accept user input and split it into command and parameter (if provided)
        user_input = input("% ").strip().split()
        
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
    config = configurations.get_config()
    print(f"Config is {config}")
    # print(availableComponents)
    go()

main()






# Print the resulting dictionary
