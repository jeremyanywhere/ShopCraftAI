import os
from openai import OpenAI
import re
import mimetypes
import configurations 
import logger 


assistants = {}
client = None
logging = logger.logger

def getClient():
    global client
    if client == None:
        client = OpenAI(api_key=configurations.getKey())
        logging.info("..getting OpenAI Client..")
    return client

def create_assistant(component):
    global assistants
    if component["name"] in assistants:
        return assistants.get(component["name"])
    assistant = getClient().beta.assistants.create(
        name=component["name"],
        instructions=component["instructions"],
        tools=[{"type": "code_interpreter"}],
        model="gpt-4o-2024-08-06"
    )
    logging.info(f"\nCreating assistant for {component['name']} - {assistant}")
    assistants[component["name"]] = assistant
    return assistant

def delete_files(id_list):
    # list all files
    #cycle through that
    # delete each one. 
    files = getClient().files
    for id in id_list:
        files.delete(id)
        logging.debug(f"Deleted file: {id}")

def delete_all_files():
    # list all files
    #cycle through that
    # delete each one. 
    files = getClient().files
    for file in files.list():
        files.delete(file.id)
        logging.debug(f"Deleted file: {file.id} - {file.filename}")

def delete_file(id):
    #deletes attached files from the server
    files = getClient().files
    try:
        files.delete(id)
    except Exception as e:
        print(f"Warning: Couldn't delete file. You may be accumulating files on the server. {e}")

def delete_assistant_output_files():
    #deletes attached files from the server
    files = getClient().files
    file_list = files.list()
    for file in file_list:
        if file.purpose == "assistants_output":
            try:
                files.delete(file.id)
            except Exception as e:
                print(f"Warning: Couldn't delete file. You may be accumulating files on the server. {e}")
          

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

def get_component_file_paths(data, component_name, visited=None, ignore = []):
    # Initialize visited set to avoid circular dependencies
    if visited is None:
        visited = set()

    # Get the base directory from the 'source' key
    base_dir = data.get("source", "")

    # Dictionary to store components by their name for fast lookup
    component_dict = {comp["name"]: comp for comp in data["components"]}
    
    # Recursive helper function to collect file paths
    def collect_file_paths(comp_name, ignore):
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
                ignore_files = False
                for suffix in ignore:
                    if filename.endswith(suffix):
                        ignore_files = True
                if not ignore_files:
                    file_path = os.path.join(full_workdir_path, filename)
                    if os.path.isfile(file_path):
                        file_paths.append(file_path)

        # Recursively collect file paths from dependencies
        for dependency in component.get("dependencies", []):
            file_paths.extend(collect_file_paths(dependency, ignore))

        return file_paths

    # Start collecting file paths from the given component
    return collect_file_paths(component_name, ignore)

def write_file(content, component, config):
    # Initialize 'directory' from 'component' and 'src' from 'config'
    directory = component.get('workdir')
    src = config.get('source')
    name = component.get('filename')
    # Print for debugging purposes
    logging.debug(f"Config passed in is {config}")
    logging.debug(f"workdir, name, and src are {directory}, {name}, and {src}")

    # Ensure the directory exists (src/directory)
    full_directory = os.path.join(src, directory)
    if not os.path.exists(full_directory):
        os.makedirs(full_directory)  # Create the directory if it doesn't exist

    # Define the full file path (src/directory/name)
    file_path = os.path.join(full_directory, name)

    try:
        with open(file_path, 'w') as file:
            file.write(content)
        return f"File '{full_directory}' has been written to '{file_path}'."
    except Exception as e:
        return f"An error occurred writing the file {full_directory}: {e}"

def set_up_run(component, config):
    asst_id = configurations.get_assistant(component["name"])
    if not asst_id:
        assistant = create_assistant(component)
        asst_id = assistant.id
        configurations.set_assistant(assistant)
    logging.debug(f"startup with assistant {assistant.id}")
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
        assistant_id=asst_id,
        instructions=component["instructions"]
    )
    if run.status == 'completed': 
        messages = client.beta.threads.messages.list(
        thread_id=thread.id
        )
        # print(f"List object type is {type (messages)}")
        # print(f"and what is this--> {messages.data[0].content[0].text.value.strip()}")
        content = extract_python_code(messages)
        resp = write_file(content, component, config)
        logging.debug(resp)
    else:
        logging.warning(f"Unexpected Run Status {run.status}")

def create_message_file_attachments(component, config, with_file = None):
    # Array to hold all file attachments (as dicts)
    #TODO.. this needs to honor the dependency list in the config, and build a dict mapping the files to their ids. 
    if with_file == None:
        all_files_and_dependencies = get_component_file_paths(config, component['name'],with_file, component['do_not_upload'])
    else:
        base_dir = config.get("source", "")
        work_dir = component.get("workdir")
        full_workdir_path = os.path.join(base_dir, work_dir,with_file)
        if os.path.isfile(full_workdir_path):
            all_files_and_dependencies = [full_workdir_path]
        else:
            print(f"File: {with_file} not found.")
            all_files_and_dependencies = [] 

    attachments = []
    filename_id_map = {}
    
    # Constant value for tools
    
    # Iterate over all files in the given directory
    for file_path in all_files_and_dependencies:
        if os.path.isfile(file_path):
            # check that the file doesn't exist before adding. 
            # Upload each file and create a dictionary with file_id and tools
            existing_uploaded_file_id = configurations.get_uploaded_file(file_path)
            if (existing_uploaded_file_id):
                file_id_to_attach = existing_uploaded_file_id
                logging.debug(f"File not uploaded, already up there - {file_path} ")
            else:    
                file = getClient().files.create(
                    file=open(file_path, "rb"),
                    purpose='assistants',
                )
                file_id_to_attach = file.id
                configurations.set_uploaded_file(file_path, file.id)

            # Append the dictionary to the attachments list
            attachments.append({
                "file_id": file_id_to_attach,
                "tools": [{"type": "code_interpreter"}]
            })
            # add it to the map so we can find it when it has been modified
            filename_id_map[file_id_to_attach] = file_path
            
    
    return attachments, filename_id_map



def write_new_file(file_id, path):
    client = getClient()
    print(f"Creating new file {path}")

    # Fetch the file content from the client
    file = client.files.content(file_id)

    try:
        # Use mimetypes to guess whether the file is text or binary
        mime_type, encoding = mimetypes.guess_type(path)
        
        # Check if the content is binary (if the mime type is None or it starts with 'text')
        is_text = mime_type and mime_type.startswith('text')

        # If it's text, decode if necessary, otherwise leave as binary
        if isinstance(file.content, bytes):
            if is_text:
                content = file.content.decode('utf-8')  # Decode text files
            else:
                content = file.content  # Keep binary content as is
        else:
            content = file.content  # Already decoded text

        # Open the file in 'x' mode for text or 'xb' mode for binary
        mode = 'x' if is_text else 'xb'
        with open(path, mode) as new_file:
            new_file.write(content)
        logging.debug(f"File successfully created at {path}")
    except FileExistsError:
        print(f"Error: File '{path}' already exists.")
    except Exception as e:
        print(f"An error occurred while writing to the file: {e}")

    return None

def rewrite_updated_file(file_id, path):
    client = getClient()
    print(f"Rewriting updated file...{path}")

    # Fetch the file content from the client
    file = client.files.content(file_id)
    logging.debug(f"File type is {type(file)} and content is: {file.content}")

    try:
        # Check if the content is in bytes and decode it to a string
        content = file.content.decode('utf-8') if isinstance(file.content, bytes) else file.content

        # Open the file at the given path and overwrite its content with the decoded content
        with open(path, 'w') as file_to_overwrite:
            file_to_overwrite.write(content)
        logging.debug(f"File successfully overwritten at {path}")
    except Exception as e:
        logging.debug(f"An error occurred while writing to the file: {e}")

    return None


def clean_up_attachments():
    #remove dirty files id from sessions.files?
    dirty_files = configurations.get_dirty_uploaded_file_ids()
    logging.debug(f"Dirty file list is: {dirty_files}")
    delete_files(dirty_files)
    configurations.remove_dirty_uploaded_file_ids()
    #remove all assistants output files. 
    delete_assistant_output_files()


def execute_prompt(component, config, user_prompt, with_file=None, no_upload = False):
    #TODO : security / sanity check on the prompt.
    #remove legacy files first
    clean_up_attachments()
    asst_id = configurations.get_assistant(component["name"])
    if not asst_id:
        assistant = create_assistant(component)
        asst_id = assistant.id
        configurations.set_assistant(assistant)
    client = getClient()
    if no_upload:
        file_attachments = []
        filename_id_map = {}
    else:
        file_attachments,filename_id_map  = create_message_file_attachments(component, config, with_file)
    logging.debug(f"ID to filename map.. {filename_id_map}")
    
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
        assistant_id=asst_id,
        instructions=
        """
            You are a code generation and editing tool, you will make changes to any attached 
            files needed, as requested. You will update each necessary file to create a new file.
            You must attach all updated files as file attachments to the message response. 
            Each updated file must be given a name which includes the id of the original file that was modified. 
            If you are asked to create an image file you don't need to use the attached files as reference.
         """
        #NB this prompt needs to mention that the result must be "attached to the message", otherwise it seems not to do that.    
            

    )
    if run.status == 'completed': 
        messages = client.beta.threads.messages.list(
        thread_id=thread.id
        )
        # print(f"List object type is {type (messages)}")
        # print(f"and what is this--> {messages.data[0].content[0].text.value.strip()}")
    else:
        print (f"Run finished unexpectedly with status {run.status}")
        return

    if messages.data is not None and len(messages.data) > 0:
        #loop through all elements of data array. 
        attachment_count = 0
        for m in range(len(messages.data)-1,-1,-1):
        # for message in messages.data:
            message = messages.data[m]
            attachments = message.attachments
            # Check if attachments is not None before trying to loop
            #TODO also check that attachments are actually file attachments. 
            if attachments is not None and len(attachments) > 0:
                for attachment in attachments:
                    attachment_count += 1
                    # Retrieve the file using the file_id from the attachment
                    file = getClient().files.retrieve(attachment.file_id)
                    if file.purpose != "assistants_output":
                        continue
                    # Iterate over the file IDs in filename_id_map and check for matches
                    file_found = False
                    # file_ids_to_remove = set()
                    for file_id in filename_id_map:
                        #print(f"Looking through the map :-{file_id}, {filename_id_map[file_id]}, file.id is {file.id} filename is {file.filename}")
                        if file_id in file.filename:
                            logging.info(f"Updating file.. {filename_id_map[file_id]} was updated.")
                            file_found = True
                            rewrite_updated_file(file.id, filename_id_map[file_id])
                            #uploaded file now out of date, remove from session persist
                            configurations.set_uploaded_file_dirty(filename_id_map[file_id]) 

                    if not file_found:
                        print(f"Downloading new file.. {file.filename}")
                        new_path = os.path.join(config['source'], component['workdir'], os.path.basename(file.filename))
                        write_new_file(file.id, new_path)  
    
            logging.debug(f"Message {message.id} - attachments: {message.attachments}")    
            print(f"{message.content[0].text.value}\n")
        if attachment_count < 1:
            print(f"Warning: No Files Updated. Try a different prompt?")
    
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

    