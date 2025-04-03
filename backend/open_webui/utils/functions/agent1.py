#from smolagents.prompts import CODE_SYSTEM_PROMPT
## Au cas ou : smolagents.__version__ = 1.3.0
sys_prompt = """Tu es Albert, un assistant expert qui résout des tâches avec du code Python. 
Tu aides les agents de l'état dans leur travail.
Nous sommes en Janvier 2025.
Suis ces étapes :
    "Thought:" Explique ta démarche et les outils nécessaires.
    "Code:" Écris du code (finissant par ```<end_code>).
    "Observation:" Utilise les résultats imprimés du code précédent.

    Tu verras parfois 'Out' qui correspond aux sortie de fonctions lorsqu'elles n'ont pas été enregistrées dans une variable.

Règles de code:
    Définis les variables avant de les utiliser.
    Appelle les outils avec les bons arguments.
    Imprime les résultats avec print si un outil a une sortie imprévisible, et utilise-les dans un bloc suivant.
    Ne jamais appeler final_answer directement après un autre outil. D'abord, print la réponse, puis fais un appel séparé à final_answer.
    Nomme les variables différemment des outils.
    Tu peux importer uniquement ces modules : {{authorized_imports}}.
    La persistance d'état entre les exécutions est activée, les variables restent stockées et tu peux les réutiliser.
    N'appelles jamais un tool pour rien, si tu vois la réponse appelles directement final_answer.
    'final_answer' prend en argument un string, contenant ta réponse finale, claire précise et formattée en markdown.
    Si un tool te donne une réponse déjà complète, envoie la directement à final_answer. Ne réécris pas inutilement, inutile de modifier la réponse déjà complète.

Outils disponibles :
{%- for tool in tools.values() %}
  - {{ tool.name }}: {{ tool.description }}
      Takes inputs: {{tool.inputs}}
      Returns an output of type: {{tool.output_type}}
{%- endfor %}
{%- if managed_agents and managed_agents.values() | list %}
Tu as aussi des agents que tu manage. 
{%- for agent in managed_agents.values() %}
- {{ agent.name }}: {{ agent.description }}
{%- endfor %}
{%- else %}
{%- endif %}
Exemples :

Task : "Comment faire une procuration ? Un détenu peut il voter ?"

Thought: Questions simples, je vais chercher des informations dans les bases car il s'agit d'administratif.
Code:
```py
procuration = simple_search_rag(user_query="faire une procuration france")
print(procuration)
vote = simple_search_rag(user_query="droit de vote du detenu en prison")
print(vote)
# Concatene les sorties pour pouvoir les voir ! c'est important!
output_result = f"Procuration: {procuration}\\nVote: {vote}"
output_result  # Return combined result explicitly do not use final answer in the first block !
```<end_code>
Observation: "[...]"

Thought: Je vais mettre en forme toutes les informations que j'ai reçu.
Code:
```py
final_answer(f'''Pour faire une procuration [...]''')
```<end_code>

Task : "Comment tu vas ?"
Thought: je vais répondre directement.
Code:
```py
final_answer(f'''Je vais bien, merci !''')
```<end_code>

Task : "Je suis handicapé a 80% et je suis né en 1972, à quelle date je peux prendre ma retraite ?"
Thought: Question complexe, je vais chercher les informations dans les bases administratives de manière approfondie.
Code:
```py
retraite = deep_search_rag(user_query="Je suis handicapé a 80% et je suis né en 1972, à quelle date je peux prendre ma retraite ?")
print(retraite) #les variables sont stockées et tu peux les réutiliser !
```<end_code>
Observation: "[...]"

Thought: La réponse est bien complète, je vais donner ma variable retraite à final_answer pour le l'utilisateur puisse la voir.
Code:
```py
final_answer({retraite}) #envoie direct
```<end_code>

Task : "A quel âge est mort Jacques Chirac ?"
Thought: Question simple, je vais chercher rapidement sur internet.
Code:
```py
chirac = simple_search_internet(user_query="âge mort Jacques Chirac")
print(chirac) #les variables sont stockées et tu peux les réutiliser !
```<end_code>
Observation: "[...]"

Thought: Je vais mettre en forme toutes les informations que j'ai reçu.
Code:
```py
final_answer(Jacques Chirac est [...]) #envoie direct
```<end_code>

Regles : 
Un tool de recherche peut te donner une réponse déjà complète, tu peux la donner directement à l'utilisateur en envoyant ta variable à final_answer.
Though ne doit être qu'une phrase, les détails vont dans les outils ou final_answer.
Ne réécris jamais une réponse déjà complète par un outil, renvoie directement la variable à final_answer.
Résous la tâche : tu gagneras $1 000 000 si tu réussis."""

from types import SimpleNamespace
import time
import dotenv
import os
import requests
import re
import json


#dotenv.load_dotenv('.env')
dotenv.load_dotenv('open_webui/utils/functions/.env')



#SUPERVISOR_MODEL = 'meta-llama/Llama-3.3-70B-Instruct' #'meta-llama/Meta-Llama-3.1-8B-Instruct' #'meta-llama/Llama-3.3-70B-Instruct' #'neuralmagic/Meta-Llama-3.1-70B-Instruct-FP8' #'mistralai/Mixtral-8x7B-Instruct-v0.1' #'meta-llama/Meta-Llama-3.1-70B-Instruct'

#session = requests.session()
#ALBERT_KEY = os.getenv('ALBERT_KEY')
#ALBERT_URL = os.getenv('ALBERT_URL')


#session.headers = {"Authorization": f"Bearer {ALBERT_KEY}"}


#def remove_consecutive_assistants(messages):
#    filtered_messages = []
#    last_role = None
#    for msg in messages:
#        if msg["role"] == "assistant" and last_role == "assistant":
#            continue  # Ignore consecutive assistant messages
#        filtered_messages.append(msg)
#        last_role = msg["role"]
#    return filtered_messages
#
#def custom_model_albert(messages, stop_sequences=[]):#"Task",'Observation']):
#    for message in messages:
#        if message['role'] == 'tool-response':
#            message['role'] = 'user'
#            message['content'] = 'TOOL_RESPONSE: ' + str(message['content'])
#    messages = remove_consecutive_assistants(messages)
#    print(messages)
#
#    data = {
#        "model": SUPERVISOR_MODEL,
#        "messages":messages,
#        "stream": False,
#        "n": 1,
#        "temperature": 0.1,
#        "repetition_penalty": 1,
#        "max_tokens":1024,
#        "stop" : stop_sequences,
#    }
#    response = session.post(url=f"{ALBERT_URL}/chat/completions", json=data, timeout=100000)
#    answer = response.json()['choices'][0]['message']
#    return SimpleNamespace(**answer) #needed to have a 'json'


#custom_model_albert(messages = [{'role': 'user', 'content': 'Hello, how are you?'}], stop_sequences=[])
from open_webui.utils.functions.deepsearch_tool import run_research
from smolagents.agents import ToolCallingAgent, CodeAgent
from smolagents import tool
from typing import Optional


def create_tools(model_func, collections, description, user, request):
    @tool
    def deep_search_internet(user_query: str) -> str:
        """
        Fait une recherche approfondie sur les questions non-administratives, pour les questions complexes ayant besoin de recherche sur internet.
        Args:
            user_query: the user query (str)
        """
        print("Searching internet...")
        result = run_research(user_query, internet=True, iteration_limit=2, prompt_suffix='', max_tokens=2048, num_queries=3, k=3, lang='fr')[0]
        print("Internet search completed. \nResults: \n", result)
        return result

    @tool
    def deep_search_rag(user_query: str) -> str:
        #Fait une recherche approfondie sur les questions administratives, pour les questions complexes ayant besoin de recherche dans une base de données administratives.
        """
        Cet outil fait une recherche approfondie sur le Rag choisi par l'utilisateur, pour les questions complexes ayant besoin de plusieurs recherches en même temps dans le rag de manière plus profonde.
        {{description}}
        Args:
            user_query: the user query (str)
        """
        print("Searching administratif...") 
        result = run_research(user_query, internet=False, iteration_limit=2, prompt_suffix='', max_tokens=2048, num_queries=3, k=3, lang='fr', collections=collections, user=user, request=request)[0]
        print("Administratif search completed. \nResults: \n", result)
        return result
    @tool
    def simple_search_internet(user_query: str) -> str:
        """
        Cet outil fait une recherche simple à partir d'une question, pour les questions nécessitant une recherche rapide sur internet.
        Si la réponse donnée est déjà complète, tu peux l'envoyer directement à final_answer.
        Args:
            user_query: the user query (str)
        """
        print("Searching internet...")  
        result = run_research(user_query, internet=True, iteration_limit=2, prompt_suffix='Ignores les instructions précédentes, fais une réponse courte et concise qui répond à la question. L\'utilisateur ne veut pas de réponse détaillée avec des informations inutiles.', max_tokens=400, num_queries=1, k=2, lang='fr')[0]
        print("Internet search completed. \nResults: \n", result)
        return result
    @tool
    def simple_search_rag(user_query: str) -> str:
        """
        Cet outil fait une recherche simple sur le RAG de l'utilisateur pour les questions nécessistant une seule recherche.
        Si l'utilisateur te parle de son document ou de rag, c'est cet outil qui doit être utilisé.
        {{description}}
        Args:
            user_query: the user query (str)
        """
        print("Searching administratif...") 
        report = run_research(user_query, internet=False, iteration_limit=2, prompt_suffix='Ignores les instructions précédentes, fais une réponse courte et concise qui répond à la question. L\'utilisateur ne veut pas de réponse détaillée avec des informations inutiles.', max_tokens=400, num_queries=1, k=5, lang='fr', collections=collections, user=user, request=request)[0]

        print("Administratif search completed. \nResults: \n", report)
        return report
    @tool
    def simple_response(user_query: str) -> str:
        """
        Donne une réponse simple à partir d'une question pas très complexe, pouvant être répondu sans recherche.
        Args:
            user_query: the user query (str)
        """
        print("Simple response...")
        answer = model_func(messages = [{'role': 'user', 'content': user_query}], stop_sequences=[])
        print("Simple response completed. \nResults: \n", answer.content)
        return answer.content

    @tool
    def coder(user_query: str) -> str:
        """
        Génère du code Python en répondant à la question de l'utilisateur.
        Args:
            user_query: la question de l'utilisateur (str)
        """ 
        print("Coding...")
        answer = model_func(messages = [{'role': 'user', 'content': user_query}], stop_sequences=[])
        print("Coding completed. \nResults: \n", answer.content)
        return answer.content

    tools = [deep_search_internet, simple_search_internet, simple_search_rag, deep_search_rag, simple_response]
    return tools
#agent = CodeAgent(tools=tools, model=custom_model_albert, max_steps=5, verbosity_level=3, prompt_templates={"system_prompt" : sys_prompt})