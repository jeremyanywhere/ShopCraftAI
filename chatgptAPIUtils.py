from openai import OpenAI

assistantsDict = {}

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

def createAssistants(components):
    client = OpenAI(api_key=getKey())
    global assistantsDict
    for component in components.values():
        assistant = client.beta.assistants.create(
            name=component["name"],
            instructions=component["instructions"],
            tools=[{"type": "code_interpreter"}],
            model="gpt-4o-2024-08-06")
        assistantsDict[component["name"]] = assistant
        print(f"\nCreating assistant for {component["name"]} - {assistant}")
    return assistantsDict

def runStartUp(component):
    client = OpenAI(api_key=getKey())
    # get instructions and create prompt from the model.
    # get the working directory to copy the created files into.
    thread = client.beta.threads.create(
        messages=[{
            "role": "user",
            "content": component["instructions"],
            "attachments": [
                {
                "tools": [{"type": "code_interpreter"}]
                }
            ]
            }
        ]
        )
    run = client.beta.threads.runs.create(
        thread_id=component["name"]+"Thread",
        assistant_id=component["name"]
)