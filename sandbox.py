import openai
import json

openai.api_key_path = './openapi_key.txt' # Your API key should be here

story = "#G25# As a repository manager, I want to know all the collections and objects in the DAMS for which I have custodial responsibility."

conversation = list()
result = dict()
result['story'] = story
tokens = { "prompts": 0, "completion": 0 }

##### Extracting concepts
print("1. Extracting concepts")
conversation.append(
    {'role': 'system', 'content': 'You are a requirements engineering assistant. You will be provided by the user a user story, and your task is to extract element from these models and call provided functions to record your findings.'})
conversation.append(
    {'role': 'system', 'content': 'You are only allowed to call the provided function in your answer'})
conversation.append(
    {'role': 'system', 'content':'The elements you are asked to extract from the stories are the following: Persona, Action, Entity, Benefit. A Story can contain multiple elements in each categories.'})
conversation.append(
    {'role': 'system', 'content': "Here is an example. In the story 'As a UI designer, I want to begin user testing, so that I can validate stakeholder UI improvement requests', the Persona is 'UI designer'. The actions are 'begin' and 'validate'. The entities are 'user testing' and 'stakeholder UI improvement requests'. The benefit is 'I can validate stakeholder UI improvement requests'"})
conversation.append({'role': 'user', 'content': "Here is the story you have to process:\n"+story})

response = openai.ChatCompletion.create(
    model = "gpt-3.5-turbo-0613",
    functions = [ 
        { "name": "record_elements",
        "description": "Record the elements extracted from a story",
        "parameters": {
            "type": "object",
            "properties": {
                "personas": {
                    "type": "array",
                    "description": "The list of personas extracted from the story",
                    "items": { "type": "string" }
                },
                "entities": {
                    "type": "array",
                    "description": "The list of entities extracted from the story",
                    "items": { "type": "string" }
                },
                "actions": {
                    "type": "array",
                    "description": "The list of actions extracted from the story",
                    "items": { "type": "string" }
                },
                "benefit": {
                    "type": "string",
                    "description": "A single string containing the benefit expected from the story",
                },
            },
            "required": ["personas", "entities", "actions", "benefit"],
        }
      }],
    messages = conversation,
    temperature=0.2)
tokens["prompts"] += int(response["usage"]["prompt_tokens"])
tokens["completion"] += int(response["usage"]["completion_tokens"])

response_message = response["choices"][0]["message"]
extracted = None
if response_message.get("function_call"):
    extracted = json.loads(response_message["function_call"]["arguments"])
result['concepts'] = extracted

#### Categorizing concepts
print("2. categorizing concepts")
conversation.append({'role': 'system', 'content': "Here are the extracted concepts:\n"+str(extracted)})
conversation.append(
  {'role': 'system', 'content': "You know need to make the difference between primary concepts and secondary concepts in the information you have extracted"}
)
conversation.append(
  {'role': 'system', 'content': "Here is an example. In the example that was given initially, the actions primary action is 'begin' and the secondary one is 'validate'. The primary entity is 'user testing' and the secondary entity is 'stakeholder UI improvement requests'."}
)

response = openai.ChatCompletion.create(
    model = "gpt-3.5-turbo-0613",
    functions = [ 
            { "name": "categorize_elements",
      "description": "Make the distinction between primary and secondary elements in a story",
      "parameters": {
          "type": "object",
          "properties": {
              "primary_entities": {
                  "type": "array",
                  "description": "The set of all primary entities in the story",
                  "items": { "type": "string" }
              },
              "secondary_entities": {
                  "type": "array",
                  "description": "The set of all secondary entities in the story",
                  "items": { "type": "string" }
              },
              "primary_actions": {
                  "type": "array",
                  "description": "The set of all primary actions in the story",
                  "items": { "type": "string" }
              },
              "secondary_actions": {
                  "type": "array",
                  "description": "The set of all secondary actions in the story",
                  "items": { "type": "string" }
              }
          },
          "required": ["primary_entities", "secondary_entities","primary_actions", "secondary_actions"],
      },
    }],
    messages = conversation,
    temperature=0.2)
response_message = response["choices"][0]["message"]
extracted = None
if response_message.get("function_call"):
    extracted = json.loads(response_message["function_call"]["arguments"])
result['categories'] = extracted
tokens["prompts"] += int(response["usage"]["prompt_tokens"])
tokens["completion"] += int(response["usage"]["completion_tokens"])

##### Extracting relations between elements
print("3. Extracting relations")
conversation.append({'role': 'system', 'content': "Here are the categorization:\n"+str(extracted)})
conversation.append({'role': 'system', 'content': "You now need to extract relationships betwen personas and actions (named trigger), and between actions and entities (named target)."})
conversation.append(
  {'role': 'system', 'content': "Here is an example. In the example that was given initially, the persona 'UI designer' triggers the action 'begin', and the action 'begin' targets the entity 'user testing'."}
)

response = openai.ChatCompletion.create(
    model = "gpt-3.5-turbo-0613",
    functions = [ 
        { 
            "name": "record_links",
            "description": "Records trigger and target links between actions, personas and entities ",
            "parameters": {
              "type": "object",
              "properties": {
                  "relations": {
                      "type": "array",
                      "description": "the link between elements",
                      "items": { 
                          "type": "object",
                          "properties": {
                              "from": { "type": "string" },
                              "to": { "type": "string" },
                              "kind": { 
                                  "type": "string", 
                                  "enum": ["triggers", "targets"] 
                              }
                          }       
                      }
                  },
            },
            "required": ["links"],
        },
      }
    ],
    messages = conversation,
    temperature=0.2)
response_message = response["choices"][0]["message"]
extracted = None
if response_message.get("function_call"):
    extracted = json.loads(response_message["function_call"]["arguments"])
result['links'] = extracted
tokens["prompts"] += int(response["usage"]["prompt_tokens"])
tokens["completion"] += int(response["usage"]["completion_tokens"])


##### Printing results & cost
result['costs'] = tokens
print(json.dumps(result, indent=2))

