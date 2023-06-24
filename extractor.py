# GPT 3.5 to support user story conceptual model extraction
# author: Sebastien Mosser

import openai
import os
import time
import json
import timeout_decorator

####
## Configuration
####

## OpenAI specific config
openai.api_key_path = './openapi_key.txt' # Your API key should be here
MODEL = 'gpt-3.5-turbo-0613'              # required to use JSON schemas

## dataset location
DATASET = './dataset/current'
START_AT = 1

       ###############################
######## Do not edit after this line ########
       ###############################

####
## Process Dataset
####

def main(dataset, model):
   print(f'START: {__stamp()}')
   process_dataset(dataset, model)
   print(f'END: {__stamp()}')

def process_dataset(directory, model):
   for file in os.listdir(directory):
      print(f'# Processing {file}')
      process_backlog(f'{directory}/{file}', model)

def process_backlog(a_backlog, model):
   global START_AT
   output_file = f'./output/{model}/{os.path.basename(a_backlog)}'
   counter = 0
   for user_story in open(a_backlog, 'r'):
      counter += 1
      if counter < START_AT:
         print(f'Skipping Story #[{counter}]')
         continue
      print(f'- Story #[{counter}] -- started at {__stamp()}')
      print(f'    - {user_story}')
      data = process_story(user_story, model)
      if (data == None):
         continue
      print(f'    - saving result into: {output_file}_{counter}.json')
      __store_result(data, f'{output_file}_{counter}.json')

####
## Business logic
####

def process_story(user_story, model):
   result = dict()
   result['story'] = user_story
   # 0. Setting up the conversational context
   cost = init_cost()
   conversation = prompt_setup()
   # 1. Extracting concepts
   prompt_for_concept_extraction(conversation, user_story)
   try:
      extracted = __call_GPT(model, conversation, record_extracted_concepts)
   except RuntimeError:
      return
   result['extraction'] = extracted['response']
   cost = update_cost(cost, extracted)
   # 2. Categorizing concepts
   prompt_for_concept_categorization(conversation, result['extraction'])
   try:
      categorized = __call_GPT(model, conversation, record_categories)
   except RuntimeError:
      return
   result['categories'] = categorized['response']
   cost = update_cost(cost, categorized)
   # 3. Extracting relations
   prompt_for_relations_extraction(conversation, result['categories'])
   try:
      relations = __call_GPT(model, conversation, record_links)
   except RuntimeError:
      return
   result['relations'] = relations['response']
   cost = update_cost(cost, relations)
   # 4. Returning result
   result['cost'] = cost
   return result

## Cost Tracker
####

def init_cost():
   return { 'input': 0, 'output': 0, 'time (ns)': 0 }

def update_cost(cost, response):
   return __update_cost(cost, 
                      int(response['input_tokens']), 
                      int(response['output_tokens']), 
                      response['timer'])

def __update_cost(cost_record, input, output, time):
   return {
      'input':  cost_record['input']  + input, 
      'output': cost_record['output'] + output, 
      'time (ns)':   cost_record['time (ns)']   + time
   }

####
## Prompts
####

def prompt_setup():
    conversation = list()
    conversation.append(
        {'role': 'system', 'content': 'You are a requirements engineering assistant specialized in agile methods and backlog management.'})
    conversation.append(
        {'role': 'system', 'content': 'You will be provided by the user a user story, and your task is to extract element from these models and call provided functions to record your findings.'})
    conversation.append(
        {'role': 'system', 'content': 'You are only allowed to call the provided function in your answer'})
    return conversation

def prompt_for_concept_extraction(conversation, story):
    conversation.append(
        {'role': 'system', 'content':'The elements you are asked to extract from the stories are the following: Persona, Action, Entity, Benefit. A Story can contain multiple elements in each categories.'})
    conversation.append(
        {'role': 'system', 'content': "Here is an example. In the story 'As a UI designer, I want to begin user testing, so that I can validate stakeholder UI improvement requests', the Persona is 'UI designer'. The actions are 'begin' and 'validate'. The entities are 'user testing' and 'stakeholder UI improvement requests'. The benefit is 'I can validate stakeholder UI improvement requests'"})
    conversation.append(
       {'role': 'user', 
        'content': f'Here is the story you have to process:\n{story}'})
    return conversation

def prompt_for_concept_categorization(conversation, extracteds):
   conversation.append(
      {'role': 'assistant', 
       'content': f'Here are the extracted concepts:\n{extracteds}'})
   conversation.append(
      {'role': 'system', 'content': "You know need to make the difference between primary concepts and secondary concepts in the information you have extracted"})
   conversation.append(
      {'role': 'system', 'content': "In the example that was given initially, the actions primary action is 'begin' and the secondary one is 'validate'. The primary entity is 'user testing' and the secondary entity is 'stakeholder UI improvement requests'."}
   )
   return conversation

def prompt_for_relations_extraction(conversation, categories):
   conversation.append(
      {'role': 'assistant',
       'content': f'Here is the categorization:\n{categories}'})
   conversation.append(
      {'role': 'system', 'content': "You now need to extract relationships betwen personas and actions (named trigger), and between actions and entities (named target)."})
   conversation.append({'role': 'system', 'content': "In the example that was given initially, the persona 'UI designer' triggers the action 'begin', and the action 'begin' targets the entity 'user testing'."})
   return conversation

####
## JSON Schemas
####

record_extracted_concepts = { 
        "name": "record_elements",
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
      }

record_categories = { 
   "name": "categorize_elements",
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
      "required": [
         "primary_entities", "secondary_entities",
         "primary_actions", "secondary_actions"
      ],
    },
  }

record_links = {
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
                  "from": { 
                     "type": "string",
                     "description": "left part of the relation"
                  },
                  "to": { 
                     "type": "string",
                     "description": "right part of the relation"
                  },
                  "kind": {
                     "type": "string", 
                     "enum": ["triggers", "targets"],
                     "description": "kind of relation: 'triggers' or 'targets'"
                  }
               }       
            }
         },
      },
      "required": ["relations"],
   },
}
  
####
## Technical functions
####

def __stamp():
   return time.strftime("%H:%M:%S", time.localtime())

def __call_GPT(model, conversation, schema):
  print(f'        - calling model {__stamp()}')
  start = time.time_ns()
  
  try:
      response = __call_with_timeout(model, conversation, schema)
  except:
      __increment_failure() # Using Circuit-breaker like
      print(f'       - exception caught! Pausing for 60 seconds')
      time.sleep(60)
      return __call_GPT(model, conversation, schema)
  
  __reset_failure()
  end = time.time_ns()
  payload = response["choices"][0]["message"]
  contents = None
  if payload.get("function_call"):
     try:
      contents = json.loads(payload["function_call"]["arguments"])
     except json.decoder.JSONDecodeError:
        print('    - /!\ Invalid JSON Detected')
        print(payload["function_call"]["arguments"])
        raise RuntimeError("Invalid JSON")
  result =  {
      'response':      contents,
      'input_tokens':  response['usage']['prompt_tokens'],
      'output_tokens': response['usage']['completion_tokens'],
      'timer':         end - start
   }
  time.sleep(2)
  return result


# We timeout on our side if the answer takes more than 30 seconds
@timeout_decorator.timeout(seconds=30) 
def __call_with_timeout(model, conversation, schema):
   response = openai.ChatCompletion.create(
      model       = model,
      functions   = [schema],
      messages    = conversation,
      temperature = 0.0 # Temperature set to 0 to be deterministic (kinda)
   )
   return response
  

def __store_result(result, file):
   with open(file, 'w') as of:
      of.write(json.dumps(result, indent=2))

####
## Circuit Breaker-like
####

__cb_counter = 0
__cb_threshold = 5

def __increment_failure():
   global __cb_counter
   __cb_counter += 1
   if __cb_counter > __cb_threshold:
      raise Exception("Circuit Breaker failed to recover")

def __reset_failure():
   global __cb_counter
   __cb_counter = 0

####
## Main dispatch magic
####

if __name__ == "__main__":
    main(DATASET, MODEL)
