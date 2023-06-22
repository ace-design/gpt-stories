import openai
import os
import time
import tiktoken
import datetime


openai.api_key_path = './openapi_key.txt' # Your API key should be here
model = "gpt-3.5-turbo"

threshold = 750
prompts = [
   "You are a requirements engineering assistant. You will be provided by the user a set of User Stories, and your task is to extract element from these models and reply in JSON format. The elements you are asked to extract from the stories are the following: Persona, Action, Entity, Benefit. A Story can contain multiple elements in each categories. ",
   "Here is an example. In the story 'As a UI designer, I want to begin user testing, so that I can validate stakeholder UI improvement requests', the Persona is 'UI designer'. The actions are 'begin' (primary) and 'validate' (secondary). The entities are 'user testing' (primary) and 'stakeholder UI improvement requests' (secondary). The benefit is 'I can validate stakeholder UI improvement requests'",
   "You also have to extract relations between elements: Triggers is a link between a Persona and an Action, and Targets is a link between an Action and a Entity. You should make a difference between primary actions and secondary actions, as well as primary entities and secondary entities.",
   "In the previous example, the persona 'UI designer' triggers the action 'begin', and the action 'begin' targets the entity 'user testing'.",
   "You have to output a single JSON document containing all the stories (no other text than the expected JSON document). For each story, you will answer the input text, the personas (an array), the actions (an array), the entities (an array), the benefit (a scalar), and the relations (triggers and targets).",
   "Do not pretty print the JSON, make it as compact as possible. And do not add any extra text around the JSON document."
]

def main():
  global model
  print('Start: ' + stamp())
  for file in os.listdir('./dataset'):
    print(f'## Processing [{file}] with [{model}]')
    stories = read_stories('./dataset/'+file)
    process(stories, f'./output/{model}/{file}')
  print('End: ' + stamp() )

def read_stories(file_name):
    with open(file_name, 'r') as file:
        return file.read()

def stamp():
   return time.strftime("%H:%M:%S", time.localtime())

def process(stories, output_file):
  global threshold
  chunks = split_data(stories)
  print(f'  Detecting {len(chunks)} chunks of {threshold} tokens')
  for idx, c in enumerate(chunks):
     print(f'  ... processing chunk #{idx} into {output_file}_{idx} \t[{stamp()}]')
     gptify(c, output_file+f'_{idx}')

def split_data(stories):
   global model, threshold
   encoding = tiktoken.encoding_for_model(model)
   nb_tokens = prompt_tokens()
   chunks = []
   current = ""
   for line in stories.splitlines():
      if line.isspace():
         continue
      if nb_tokens >= threshold:
          chunks.append(current)
          current = ""
          nb_tokens = prompt_tokens()
      nb_tokens += len(encoding.encode(f'{line}\n'))
      current += f'{line}\n'
   chunks.append(current)
   return chunks

def prompt_tokens():
   global prompts, model
   encoding = tiktoken.encoding_for_model(model)
   tokens = len(encoding.encode(''.join(prompts)))
   return int(tokens*1.05) # 5% safety margin

def build_prompt():
  global prompts
  msg = []
  for p in prompts:
    msg.append({"role": "system", "content": p})
  return msg

def gptify(chunk, output_file):
  global model, prompts
  prompt = build_prompt()
  prompt.append({"role": "user",   "content": "Here is the set of stories you have to process:\n" + chunk})
  start = time.time()
  response = openai.ChatCompletion.create(
    model = model,
    messages = prompt,
    temperature = 0.0,
    
  )
  stop = time.time()
  save_result(output_file, response, stop-start)

def save_result(output_file, response, timer):
  with open(output_file, "w") as of:
    of.write("### Content\n")
    of.write(response['choices'][0]['message']['content']+"\n")
    of.write("### Finish reason: " + response['choices'][0]['finish_reason']+"\n")
    of.write("### Cost"+"\n")
    of.write(str(response['usage'])+"\n")
    of.write("### Time"+"\n")
    of.write(str(timer)+"\n")

if __name__ == "__main__":
    main()
