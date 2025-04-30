from open_webui.utils.functions.deepsearch_tool import run_research
from smolagents import tool
from open_webui.utils.functions.annuaire_tool import annuaire_check
from open_webui.utils.functions.prompts.code_agent_V2 import sys_prompt #Important, used by the frontend
## smolagents.__version__ = 1.3.0

def create_tools(model_func, collections, description, user, request, event_emitter, agent_type="bob"):
    @tool
    def deep_search_internet(user_query: str) -> str:
        """
        Fait une recherche approfondie sur les questions non-administratives, pour les questions complexes ayant besoin de recherche sur internet.
        A utiliser uniquement pour des questions complexes, qui ont besoin de multiple recherches sur internet.
        Output : une chaine de caractères contenant les informations trouvées.
        Args:
            user_query: une question claire et précise (str)
        """
        print("Searching internet...")
        result = run_research(user_query, internet=True, iteration_limit=2, prompt_suffix='', max_tokens=2048, num_queries=3, k=3, lang='fr', event_emitter=event_emitter)[0]
        print("Internet search completed. \nResults: \n", result)
        return result

    @tool
    def deep_search_rag(user_query: str) -> str:
        """
        TMP DESC
        Args:
            user_query: une question claire et précise (str)
        """
        print("Searching administratif...") 
        result = run_research(user_query, internet=False, iteration_limit=2, prompt_suffix='', max_tokens=2048, num_queries=3, k=3, lang='fr', collections=collections, user=user, request=request, event_emitter=event_emitter)[0]
        print("Administratif search completed. \nResults: \n", result)
        return result
    #Dynamic description from the Valves on the front
    deep_search_rag.description = f"""
Cet outil fait une recherche approfondie sur le Rag choisi par l'utilisateur, pour les questions complexes ayant besoin de plusieurs recherches en même temps dans le rag de manière plus profonde.
{description}
Args:
    user_query: une question claire et précise (str)
        """
    @tool
    def simple_search_internet(user_query: str) -> str:
        """
        Cet outil fait une recherche simple à partir d'une question, pour les questions nécessitant une recherche rapide sur internet.
        Si la réponse donnée est déjà complète, tu peux l'envoyer directement à final_answer.
        Output : une chaine de caractères contenant les informations trouvées.
        Args:
            user_query: une question claire et précise (str)
        """
        print("Searching internet...")  
        result = run_research(user_query, internet=True, iteration_limit=2, prompt_suffix='Ignores les instructions précédentes, fais une réponse courte et concise qui répond à la question. L\'utilisateur ne veut pas de réponse détaillée avec des informations inutiles.', max_tokens=400, num_queries=1, k=2, lang='fr', event_emitter=event_emitter)[0]
        print("Internet search completed. \nResults: \n", result)
        return result
    @tool
    def simple_search_rag(user_query: str) -> str:
        
        """
        TMP DESC
        Args:
            user_query: une question claire et précise (str)
        """
        print("Searching administratif...") 
        report = run_research(user_query, internet=False, iteration_limit=2, prompt_suffix='Ignores les instructions précédentes, fais une réponse directe à la question. L\'utilisateur ne veut pas de réponse détaillée avec des informations inutiles. Donnes uniquement les détails importants. Donnes toujours tes sources à la fin de ta réponse avec une partie "Sources : ", et mets [1], [2] etc au sein du texte quand tu cites une source. Dans la partie sources écris [1] [nom de l\'url](https://...) etc, appelles bien tous les liens avec un nom, l\'ordre des sources doit être le même que dans ton contexte.', max_tokens=400, num_queries=1, k=5, lang='fr', collections=collections, user=user, request=request, event_emitter=event_emitter)[0]

        print("Administratif search completed. \nResults: \n", report)
        return report
    #Dynamic description from the Valves on the front
    simple_search_rag.description = f"""
Cet outil fait une recherche simple sur le RAG de l'utilisateur pour les questions nécessistant une seule recherche.
Si l'utilisateur te parle de son document ou de rag, c'est cet outil qui doit être utilisé.
{description}
Args:
    user_query: une question claire et précise (str)
        """
    #This tool could be used in the future with a specialized code model
    @tool
    def coder(user_query: str) -> str:
        """
        Génère du code Python en répondant à la question de l'utilisateur.
        Args:
            user_query: une question claire et précise (str)
        """ 
        print("Coding...")
        answer = model_func(messages = [{'role': 'user', 'content': user_query}], stop_sequences=[])
        print("Coding completed. \nResults: \n", answer.content)
        return answer.content

    @tool
    def annuaire_administratif(what: str) -> str:
        """
        Cherches des informations sur une personne dans l'annuaire administratif où sur un lieu. Renvoi les informations trouvées.
        Quand l'utilisateur te demande des information sur quelqu'un, demande toujours si tu dois chercher dans l'annuaire administratif ou sur internet.
        N'utilise cet outil QUE pour des personnes ou des lieux administratifs, si tu as un doutes sur un personne demande a l'utilisateur de préciser si il parle d'administratif ou non en lui envoyant un message avec final_answer.
        Output : une chaine de caractères contenant les informations trouvées.
        Args:
            what: Le nom d'une personne (NOM PRENOM) ou d'un lieu administratif et rien d'autre. (str)
        """
        print("Annuaire administratif...")
        answer = annuaire_check(what=what, where="")
        print("Annuaire administratif completed. \nResults: \n", answer)
        return "Résumes ces informations pour l'utilisateur : " + str(answer) + "\n\nVoilà ce qui a été trouvé pour ta requête, résumes ces informations pour l'utilisateur si elles sont pertinentes. RESUMES CES INFOS NE RENVOIE PAS CELA COMME TEL"

    # Here we define the tools list for each type of agent
    if agent_type == "rag":
        tools = [simple_search_internet, simple_search_rag, deep_search_rag]
    elif agent_type == "bob":
        tools = [annuaire_administratif, simple_search_rag, deep_search_rag, deep_search_internet, simple_search_internet]
    return tools
#Agent is now instanciated on the front