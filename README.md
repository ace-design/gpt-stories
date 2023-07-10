# Extracting Domain Models from User Stories using (chat)GPT 3.5

## General Info

- Author: [Sébastien Mosser](mossers@mcmaster.ca), McMaster University & McSCert
- License: [MIT](./LICENSE)
- Version: 1.0 (July 2023)

## Installation

First, install the dependencies using `pipenv`:

```
mosser@azrael gpt-stories % pipenv install
```

Once the dependencies are installed, start a pipenv shell

```
mosser@azrael gpt-stories % pipenv shell
Launching subshell in virtual environment...
 . /Users/mosser/.local/share/virtualenvs/gpt-stories-iHWjazbU-python/bin/activate
mosser@azrael gpt-stories %  . /Users/mosser/.local/share/virtualenvs/gpt-stories-iHWjazbU-python/bin/activate
(gpt-stories) mosser@azrael gpt-stories % 
```

## Usage

The code assumes your OpenAI API key is located in a file name `openapi_key.txt` at the root of this repository, and that you are currently in a pipenv shell environment.

By default, the code points to the files located in `dataset/small` (2 backlogs, 2 stories/backlog), to save token usage. 

```
(gpt-stories) mosser@azrael gpt-stories % python extractor.py 
START: 14:05:52
# Processing sample_2.txt
- Story #[1] -- started at 14:05:52
    - #G25# As a repository manager, I want to know all the collections and objects in the DAMS for which I have custodial responsibility. 

        - calling model 14:05:52
        - calling model 14:05:56
        - calling model 14:06:00
    - saving result into: ./output/gpt-3.5-turbo-0613/sample_2.txt_1.json
...
END: 14:06:40
```

Simply edit the `DATASET` global variable to point to the directory of your choice. The script will process each file in the directory as a backlog, with one user story per line.

If you need to start your analysis at a given location (_e.g._, after a server-side error), edit the `START_AT` variable.

As of OpenAI pricing model (July 2023), processing the whole backlog costs lest than $5 (USD).

## Output File Format

```json
{
  "story": "As a UI designer, I want to begin user testing, so that I can validate stakeholder UI improvement requests.\n",
  "extraction": {
    "personas": [ "UI designer" ],
    "entities": [ "user testing", "stakeholder UI improvement requests" ],
    "actions":  [ "begin", "validate" ],
    "benefit":  "I can validate stakeholder UI improvement requests"
  },
  "categories": {
    "primary_entities":   [ "user testing" ],
    "secondary_entities": [ "stakeholder UI improvement requests" ],
    "primary_actions":    [ "begin" ],
    "secondary_actions":  [ "validate" ]
  },
  "relations": {
    "relations": [
      { "from": "UI designer", "to": "begin", "kind": "triggers" },
      { "from": "begin", "to": "user testing", "kind": "targets" }
    ]
  },
  "cost": {
    "input": 1301,
    "output": 174,
    "time (ns)": 4516597000
  }
}
```
