import os
from typing import List
from openai import OpenAI
import re

from pydantic import BaseModel

class SourceCodeFile(BaseModel):
    filename: str
    original_file_id: str
    new: bool
    content: str

class CodeUpdateResponse(BaseModel):
    message_id: str
    message_text: str
    updated_files: List[SourceCodeFile]


assistants = {}
client = None


def getKey():
    try:
        with open("key.txt", 'r') as file:
            api_key = file.readline().strip()  # Read the first line and strip any extra whitespace/newline
            return api_key
    except FileNotFoundError:
        print(f"Error: Missing key.txt file. Please create a key.txt file with your ChatGPT key in it")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None
    
def getClient():
    global client
    if client == None:
        client = OpenAI(api_key=getKey())
        print("..getting OpenAI Client..")
    return client

def get_assistant(component):
    global assistants
    if component["name"] in assistants:
        return assistants.get(component["name"])
    assistant = getClient().beta.assistants.create(
        name=component["name"],
        instructions=component["instructions"],
        tools=[{"type": "code_interpreter"}],
        model="gpt-4o-2024-08-06"
    )
    print(f"\nCreating assistant for {component['name']} - {assistant}")
    assistants[component["name"]] = assistant
    return assistant



def extract_python_code(messages):
    """
    Extracts Python code from the content of a message object.
    
    Args:
        message (object): A message object containing content with Python code.
        
    Returns:
        str: The extracted Python code, or an empty string if no code is found.
    """
    code_blocks = []

    # Loop through the content of the message
    for content_block in messages.data[0].content:
        # Check if the content is a text block and contains Python code
        if hasattr(content_block, 'text') and hasattr(content_block.text, 'value'):
            # Use regex to find code enclosed in ```python ... ```
            match = re.search(r"```python(.*?)```", content_block.text.value, re.DOTALL)
            if match:
                code_blocks.append(match.group(1).strip())

    # Join all code blocks and return
    return "\n\n".join(code_blocks) if code_blocks else ""

def get_component_file_paths(data, component_name, visited=None):
    # Initialize visited set to avoid circular dependencies
    if visited is None:
        visited = set()

    # Get the base directory from the 'source' key
    base_dir = data.get("source", "")

    # Dictionary to store components by their name for fast lookup
    component_dict = {comp["name"]: comp for comp in data["components"]}
    
    # Recursive helper function to collect file paths
    def collect_file_paths(comp_name):
        if comp_name in visited:
            return []  # Avoid revisiting components

        visited.add(comp_name)  # Mark the component as visited

        # Find the component by name
        component = component_dict.get(comp_name)
        if not component:
            return []  # Component not found

        workdir = component.get("workdir")
        file_paths = []

        # Check if the directory exists, then list all files in the directory
        full_workdir_path = os.path.join(base_dir, workdir)
        if os.path.exists(full_workdir_path) and os.path.isdir(full_workdir_path):
            for filename in os.listdir(full_workdir_path):
                file_path = os.path.join(full_workdir_path, filename)
                if os.path.isfile(file_path):
                    file_paths.append(file_path)

        # Recursively collect file paths from dependencies
        for dependency in component.get("dependencies", []):
            file_paths.extend(collect_file_paths(dependency))

        return file_paths

    # Start collecting file paths from the given component
    return collect_file_paths(component_name)

def write_file(content, component, config):
    # Initialize 'directory' from 'component' and 'src' from 'config'
    directory = component.get('workdir')
    src = config.get('source')
    name = component.get('filename')

    # Print for debugging purposes
    print(f"Config passed in is {config}")
    print(f"workdir, name, and src are {directory}, {name}, and {src}")

    # Ensure the directory exists (src/directory)
    full_directory = os.path.join(src, directory)
    if not os.path.exists(full_directory):
        os.makedirs(full_directory)  # Create the directory if it doesn't exist

    # Define the full file path (src/directory/name)
    file_path = os.path.join(full_directory, name)

    try:
        with open(file_path, 'w') as file:
            file.write(content)
        return f"File '{name}' has been written to '{file_path}'."
    except Exception as e:
        return f"An error occurred: {e}"

def run_set_up(component, config):
    assistant = get_assistant(component)
    print(f"startup with assistant {assistant.id}")
    client = getClient()
    # get instructions and create prompt from the model.
    # get the working directory to copy the created files into.
    
    #ChatGPT Assistant stuff. Create Thread.
    thread = client.beta.threads.create()
    _ = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=component["createPrompt"]
        )
   
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=assistant.id,
        instructions=component["instructions"]
    )
    if run.status == 'completed': 
        messages = client.beta.threads.messages.list(
        thread_id=thread.id
        )
        # print(f"List object type is {type (messages)}")
        # print(f"and what is this--> {messages.data[0].content[0].text.value.strip()}")
        content = extract_python_code(messages)
        write_file(content, component, config)
    else:
        print(run.status)

def create_message_file_attachments(component, config):
    # Array to hold all file attachments (as dicts)
    #TODO.. this needs to honor the dependency list in the config, and build a dict mapping the files to their ids. 
    all_files_and_dependencies = get_component_file_paths(config, component['name'])
    attachments = []
    filename_id_map = {}
    directory = f"{component.get('workdir')}/{component.get('filename')}"
    
    # Constant value for tools
    #tools_value = [{"type": "function"}]
    tools_value = [
    {
      "type": "function",
      "function": {
        "name": "get_current_temperature",
        "description": "Get the current temperature for a specific location",
        "parameters": {
          "type": "object",
          "properties": {
            "location": {
              "type": "string",
              "description": "The city and state, e.g., San Francisco, CA"
            },
            "unit": {
              "type": "string",
              "enum": ["Celsius", "Fahrenheit"],
              "description": "The temperature unit to use. Infer this from the user's location."
            }
          },
          "required": ["location", "unit"]
        }
      }
    }]
    
    # Iterate over all files in the given directory
    for file_path in all_files_and_dependencies:
        if os.path.isfile(file_path):
            # Upload each file and create a dictionary with file_id and tools
            file = getClient().files.create(
                file=open(file_path, "rb"),
                purpose='assistants',
            )
            # Append the dictionary to the attachments list
            attachments.append({
                "file_id": file.id,
                "tools": [{"type": "code_interpreter"}]
            })
            # add it to the map so we can find it when it has been modified
            filename_id_map[file.id] = file_path
    
    return attachments, filename_id_map

def rewrite_updated_file(file_id, path):
    client = getClient()
    print("Rewriting updated file...")

    # Fetch the file content from the client
    file = client.files.content(file_id)
    print(f"File type is {type(file)} and content is: {file.content}")

    try:
        # Check if the content is in bytes and decode it to a string
        content = file.content.decode('utf-8') if isinstance(file.content, bytes) else file.content

        # Open the file at the given path and overwrite its content with the decoded content
        with open(path, 'w') as file_to_overwrite:
            file_to_overwrite.write(content)
        print(f"File successfully overwritten at {path}")
    except Exception as e:
        print(f"An error occurred while writing to the file: {e}")

    return None




def execute_prompt(component, config, user_prompt):
    #TODO : security / sanity check on the prompt.
    assistant = get_assistant(component)
    client = getClient()
    file_attachments,filename_id_map  = create_message_file_attachments(component, config)
    print(f"ID to filename map.. {filename_id_map}")
    
    #ChatGPT Assistant stuff. Create Thread.
    thread = client.beta.threads.create()
    _ = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_prompt,
        attachments = file_attachments
        )
    
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=assistant.id,
        instructions=
        """
            You are a code generation and editing tool, you will make changes to any attached 
            files needed, as requested. You will update each necessary file to create a new file.
            You must attach all new, updated files as file attachments to the message response. 
            Each updated file must be given a name which includes the id of the original file that was modified. 
         """
        #NB this prompt needs to mention that the result must be "attached to the message", otherwise it seems not to do that.    
            

    )
    if run.status == 'completed': 
        messages = client.beta.threads.messages.list(
        thread_id=thread.id
        )
        # print(f"List object type is {type (messages)}")
        # print(f"and what is this--> {messages.data[0].content[0].text.value.strip()}")
    # TODO put in some proper error detection, making sure return values are ok, run status is valid etc. 


    if messages.data is not None and len(messages.data) > 0:
        attachments = messages.data[0].attachments
    # Check if attachments is not None before trying to loop
        if attachments is not None and len(attachments) > 0:
            for attachment in attachments:
                # Retrieve the file using the file_id from the attachment
                file = getClient().files.retrieve(attachment.file_id)
                print(f"Lo. We have a file {file}, what's in the map? {filename_id_map}")
                # Iterate over the file IDs in filename_id_map and check for matches
                for file_id in filename_id_map:
                    print(f"Looking through the map :-{file_id}, {filename_id_map[file_id]}, file.id is {file.id} filename is {file.filename}")
                    if file_id in file.filename:
                        print(f"Updating file.. {filename_id_map[file_id]} was updated.")
                        rewrite_updated_file(file.id, filename_id_map[file_id])

        else:
            print(f"Warning: No Files Updated. Try a different prompt?")

        for mess in (messages.data):
            print(f"Message {mess.id} - attachments: {mess.attachments}")
            print(f"{mess.content[0].text.value}\n")

    
    else:
        print(f"Error: No messages returned. Run Status is: {run.status}")



    
    # Create an assistant using the collected file IDs
    # assistant = client.beta.assistants.create(
    #     instructions="You are a personal math tutor. When asked a math question, write and run code to answer the question.",
    #     model="gpt-4o",
    #     tools=[{"type": "code_interpreter"}],
    #     tool_resources={
    #         "code_interpreter": {
    #             "file_ids": file_ids
    #         }
    #     }
    # )
    
    # return assistant
    