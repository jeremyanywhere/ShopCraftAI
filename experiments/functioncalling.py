#should not be checked in
from pydantic import BaseModel
from openai import OpenAI

class Book(BaseModel):
    author: str
    title: str


def go(): 
    

    assistant = client.beta.assistants.create(
    name="Function Caller",
    instructions="You are an assistant who will use a function call to convert temperature",
    tools=[ {
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
    }],
    model="gpt-4o-2024-08-06"
    )
    thread = client.beta.threads.create()
    _ = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content="What's the weather in San Francisco today and the likelihood it'll rain?",
        attachments = [],
        )
    
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=assistant.id,
        instructions=
        """
            you will answer the question by calling the function as necessary. 
         """
        #NB this prompt needs to mention that the result must be "attached to the message", otherwise it seems not to do that.    
            

    )
    if run.status == 'completed': 
        messages = client.beta.threads.messages.list(
        thread_id=thread.id
        )