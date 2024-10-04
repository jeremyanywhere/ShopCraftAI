import os
from openai import OpenAI

import re

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

def get_message_file_attachments(directory):
    # Array to hold all file attachments (as dicts)
    attachments = []
    
    # Constant value for tools
    tools_value = [{"type": "code_interpreter"}]
    
    # Iterate over all files in the given directory
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            # Upload each file and create a dictionary with file_id and tools
            file = getClient().files.create(
                file=open(file_path, "rb"),
                purpose='assistants'
            )
            # Append the dictionary to the attachments list
            attachments.append({
                "file_id": file.id,
                "tools": tools_value
            })
    
    return attachments

def execute_prompt(directory, component, user_prompt):
    #todo : security / sanity check on 
    assistant = get_assistant(component)
    client = getClient()
    file_attachments = get_message_file_attachments(directory)
    
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
        instructions="You are a code generation and editing tool, please analyse the attached code files, making the requested changes in the relevant files and attaching the complete, new updated files for download "
    )
    if run.status == 'completed': 
        messages = client.beta.threads.messages.list(
        thread_id=thread.id
        )
        # print(f"List object type is {type (messages)}")
        # print(f"and what is this--> {messages.data[0].content[0].text.value.strip()}")

    else:
        print(run.status)
    print(f"Here we go again: ", messages)

    
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
    