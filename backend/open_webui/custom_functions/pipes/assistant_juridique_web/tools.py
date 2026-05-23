import dotenv
import os
import requests
import aiohttp
import time
from bs4 import BeautifulSoup
import asyncio
import threading
import uvloop
import re

dotenv.load_dotenv('open_webui/custom_functions/.env')

BRAVE_KEY =  os.getenv('BRAVE_KEY')
# For the citations
def extract_first_url(text):
    """
    Extracts the first URL found in a string.
    
    Args:
        text (str): The string to search for URLs
        
    Returns:
        str or None: The first URL found, or None if no URL is found
    """
    # Regular expression pattern to match URLs
    # This pattern matches http, https, ftp URLs with various domain formats
    url_pattern = re.compile(
        r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)',
        re.IGNORECASE
    )
    
    # Find the first match
    match = url_pattern.search(text)
    
    if match:
        return match.group(0)  # Return the matched URL
    else:
        return None



class Prompts:
    @staticmethod
    def researcher(num_queries, lang='fr'):
        if lang == 'en':
            return f"""You are an expert research assistant. Based on the user's request, generate up to {num_queries} distinct and simple google queries that would help gather information on the requested topic. Include keywords from the user's question in your google queries. If the user does not specify their country, assume they are from the United States and their request is in English. Respond only with a Python list, for example: ["query1", "query2"] and nothing else. The queries should not be similar."""
        return f"""Tu es un assistant expert en recherche. En te basant sur la demande utilisateur, génère jusqu'à {num_queries} distinctes
        différentes et simples queries google (comme un humain le ferait) qui aideraient à recueillir des informations sur le sujet demandé. Dans tes queries google mets aussi les mots clés présents dans la question de l'utilisateur.
        Si l'utilisateur ne précise pas son pays, part du principe qu'il est Français et que sa demande est en France.
        Réponds uniquement avec une liste python, par exemple : ["query1", "query2"] et ne dis rien d'autre. Les queries google ne doivent pas se ressembler."""
    
    @staticmethod
    def evaluator(lang='fr'):
        if lang == 'en':
            return """You are a critical research evaluator. Given the user's query and the content of a web page, determine if the web page contains useful information to answer the query. You only see an excerpt of the page. Respond with exactly one word: 'yes' if the page is useful or relevant to the query, or 'no' if it is not or does not seem useful. Do not include any additional text."""
        return """Vous êtes un évaluateur critique de recherche. Étant donné la requête de l'utilisateur et le contenu d'une page web,
        déterminez si la page web contient des informations utiles pour répondre à la requête. Vous ne voyez ici qu'un extrait de la page.
        Répondez avec exactement un mot : 'oui' si la page est utile ou en lien avec la requête, ou 'non' si elle ne l'est pas ou n'a pas l'air utile. N'incluez aucun texte supplémentaire."""

    @staticmethod
    def extractor(lang='fr'):
        if lang == 'en':
            return """You are an expert in information extraction. Based on the user's request that led to this page and its content, extract and summarize all the information that could help answer the user's request. Respond only with the summary of the relevant context without additional comments. Keep only what is related to the user's query. Also provide the titles of the articles and the complete URLs in your response, starting the response with 'According to [title or url].' when possible. Eliminate all articles that do not discuss interesting things for the user's question. If nothing is interesting for the user, respond <next>."""
        return """Tu es un expert en extraction d'information, en te basant sur la demande utilisateur qui a amené à cette page, et son contenu, extrait et résume toutes les informations qui pourraient aider à répondre à la demande utilisateur.
        Réponds uniquement avec le résumé du contexte pertinent sans commentaire supplémentaire. Ne gardes que ce qui est en lien avec la requête utilisateur. Donnes toutes les informations intéressantes pour l'utilisateur.
        Elimine tous les contextes qui ne parle pas de choses intéressantes pour la question de l'utilisateur. Si rien n'est intéressant pour l'utilisateur, réponds <suivant>. RAPPEL: Ton but n'est pas de répondre à l'utilisateur, mais d'extraitre les informations pouvant aider à répondre à la requête utilisateur."""

    @staticmethod
    def analytics(lang='fr'):
        if lang == 'en':
            return """You are an analytical research assistant. Based on the initial query, the searches conducted so far, and the contexts extracted from web pages, determine if further research is necessary to fully answer the user's query. If the context allows answering the user, respond []. Do not conduct unnecessary research. If the extracted contexts are empty or if further research is absolutely necessary, provide up to two new search queries in the form of a Python list (e.g., ["new query1", "new query2"]). If no further research is needed, respond only with an empty list []. Display only a Python list or [] without any additional text."""
        return """Vous êtes un assistant de recherche analytique. Sur la base de la requête initiale, des recherches effectuées jusqu'à présent et des contextes extraits des pages web, déterminez si des recherches supplémentaires sont nécessaires. 
        Si le contexte permet de répondre à l'utilisateur, répondez []. Ne fais pas de recherches inutiles.
        Si les contextes extraits sont vides ou si des recherches supplémentaires sont absolument nécessaires, fournissez jusqu'à deux nouvelles requêtes de recherche sous forme de liste Python (par exemple, ["new query1", "new query2"]). Si aucune recherche supplémentaire n'est nécessaire répondez uniquement avec une liste vide []. N'affichez qu'une liste Python ou une liste vide[] sans aucun texte supplémentaire.
        Ne fais jamais de recherches supplémentaires si le contexte est suffisant pour répondre à la question.
        """

    @staticmethod
    def redactor(lang='fr'):
        if lang == 'en':
            return """You are an expert in drafting user request responses. Be polite. Based on the contexts gathered above and the initial query, write a complete, well-structured, and detailed response in markdown that answers the question thoroughly. Do not make an introduction, start directly with the answer. Include references in the form '[reference number]' in the paragraphs you write that refer to the references used. Include all useful information and conclusions without additional comments, as well as the names of articles and URLs present in the context that seem relevant. In the references, make sure not to duplicate and not to have more than 5, prioritizing URLs and titles. Start with the direct answer. Then detail."""
        return """Vous êtes un expert en rédaction de réponses de demande utilisateur. Soyez poli.
        Sur la base des contextes rassemblés ci-dessus et de la requête initiale, rédigez une réponse complete, 
        bien structurée en markdown et détaillée qui répond à la question de manière approfondie. Ne faites pas d'introduction, commencez tout de suite avec la réponse. Incluez des références sous la forme '[numero reference]' dans les paragraphes que vous rédigez qui renvoient aux références utilisées.
        Incluez toutes les informations et conclusions utiles sans commentaires supplémentaires, ainsi que les noms d'articles et urls présents dans le contexte qui semble pertinents. Dans les références veillez a ne pas faire de doublons et a ne pas en avoir plus de 5 et priorisez les URLs et les titres. Commences avec la réponse sans titre ou introduction. Détailles ensuite.
        """

class TokenCounter:
    def __init__(self):
        self.lock = asyncio.Lock()
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    async def update_tokens(self, input_tokens, output_tokens):
        async with self.lock:
            self.total_input_tokens += input_tokens
            self.total_output_tokens += output_tokens

    async def get_totals(self):
        async with self.lock:
            return self.total_input_tokens, self.total_output_tokens

class AsyncHelper:
    @staticmethod
    async def call_openrouter_async(client, token_counter, messages, max_tokens=2048, step=False):
        await asyncio.sleep(1)  # Using asyncio.sleep instead of time.sleep for async code
        model = {
            'END': os.getenv('REDACTOR_MODEL'),
            'ANALYTICS': os.getenv('ANALYTICS_MODEL')
        }.get(step, os.getenv('DEFAULT_MODEL'))

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.1,
        }
        try:
            #async with client.chat.completions.create(**payload) as resp:
            resp = client.chat.completions.create(**payload) 
            print("RESSSPPPP : ", resp)
            if resp: #.status == 200:
                result = resp #.json()
                try:
                    answer = result.choices[0].message.content #['choices'][0]['message']['content']
                    input_tokens = result.usage.prompt_tokens
                    output_tokens = result.usage.completion_tokens
                    await token_counter.update_tokens(input_tokens, output_tokens)
                    return answer
                except (KeyError, IndexError):
                    print("Unexpected OpenRouter response structure:", result)
                    return None
            else:
                text = await resp.text()
                print(f"OpenRouter API error: {resp.status} - {text}")
                return None
        except Exception as e:
            print("Error calling OpenRouter:", e)
            return None

    @staticmethod
    async def generate_search_queries_async(client, token_counter, user_query, num_queries=2, lang='fr'):
        prompt = Prompts.researcher(num_queries, lang)
        messages = [
            {"role": "system", "content": "You are a precise and helpful search assistant." if lang == 'en' else "Vous êtes un assistant de recherche précis et utile."},
            {"role": "user", "content": f"{prompt}\nDemande utilisateur: {user_query}\n Liste python de la ou les requête(s) google:\n"}
        ]
        print("RESEARCHER PROMPT")
        print(messages)
        response = await AsyncHelper.call_openrouter_async(client, token_counter, messages, max_tokens=150)
        #print(response)
        if response:
            try:
                search_queries = eval(response)
                if isinstance(search_queries, list):
                    return search_queries
                else:
                    print("LLM did not return a list. Response:", response)
                    return []
            except Exception as e:
                print("Error parsing search queries:", e, "\nResponse:", response)
                return []
        return []

    @staticmethod
    async def perform_brave_search_async(client, query, k=2, num_queries=2):
        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": BRAVE_KEY
        }
        params = {
            "q": query,
            "search_lang": "fr",
            "count": k,
            "country": "fr",
            "goggles": ["https://gist.github.com/camilleAND/751a30edc9ae6304b345750ff77ba0dd"]
        }
        try:
            resp = requests.get(url, headers=headers, params=params)
            if resp.status_code == 200:
                results = resp.json()
                links = [result.get('url') for result in results.get('web', {}).get('results', [])]
                print("="*12)
                print(links)
                print("="*12)
                if num_queries > 1:
                    time.sleep(1)
                return links[:k]
            else:
                text = resp.text
                print(f"Brave search API error: {resp.status_code} - {text}")
                return []
        except Exception as e:
            print("Error performing Brave search:", e)
            return []


    @staticmethod
    def webpage_to_human_readable(page_content):
        soup = BeautifulSoup(page_content, 'html.parser')
        # Remove non-content elements
        for element in soup(['script', 'style', 'meta', 'link', 'noscript', 'header', 'footer', 'aside']):
            element.decompose()
        text = soup.get_text(separator='\n')
        # Clean up whitespace
        cleaned_text = '\n'.join(line.strip() for line in text.splitlines() if line.strip())
        return cleaned_text

    @staticmethod
    async def fetch_webpage_text_async(url):
        try:
            #async with requests.get(url, timeout=10) as resp:  # Added timeout
            headers = {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
            }
            resp = requests.get(url, headers=headers, timeout=10)
            if resp: #.status == 200:
                page_content = resp.text#()
                return AsyncHelper.webpage_to_human_readable(page_content)
            else:
                print(f"Fetch error for {url}: {resp}")
                return ""
        except Exception as e:
            print(f"Error fetching webpage text for {url}:", e)
            return ""

    @staticmethod
    async def is_page_useful_async(client, token_counter, user_query, page_text, lang='fr'):
        print("ASKING EVALUATOR")
        if not page_text:
            print("EVALUATOR RESPONSE: page_text is empty")
            return "Non"
            
        prompt = Prompts.evaluator(lang)
        messages = [
            {"role": "system", "content": "You are a strict and precise evaluator of research relevance." if lang == 'en' else "Vous êtes un évaluateur strict et précis de la pertinence des recherches."},
            {"role": "user", "content": f"Requête utilisateur: {user_query}\n\nExtrait de page web (premiers 2000 caractères) :\n{page_text[:2000]}[...] \n\n{prompt}"}
        ]
        response = await AsyncHelper.call_openrouter_async(client, token_counter, messages, max_tokens=10)
        print(f"EVALUATOR RESPONSE: {response}")
        if response:
            answer = response.strip().lower()
            print("Useful?:", answer)
            return "Oui" if "oui" in answer or "yes" in answer else "Non"
        return "Non"

    @staticmethod
    async def extract_relevant_context_async(client, token_counter, user_query, search_query, page_text, link, max_tokens=1024, lang='fr'):
        if not page_text:
            return ""
            
        prompt = Prompts.extractor(lang)
        messages = [
            {"role": "system", "content": "You are an expert in information extraction and synthesis." if lang == 'en' else "Vous êtes un expert dans l'extraction et la synthèse d'informations."},
            {"role": "user", "content": f"Requête utilisateur: {user_query}\nRequête de recherche: {search_query}\n\nContexte trouvé (premiers 20000 caractères) :\n{page_text[:20000]}\n\n{prompt}"}
        ]
        response = await AsyncHelper.call_openrouter_async(client, token_counter, messages, max_tokens=max_tokens)
        if response:
            print("EXTRACTOR RESPONSE")
            print(response)
            print("="*12)
            print("END EXTRACTOR RESPONSE")
            return "[" + link + "]" + response.strip()
        return ""

    @staticmethod
    async def get_new_search_queries_async(client, token_counter, user_query, previous_search_queries, all_contexts, lang='fr'):
        if not all_contexts:
            # If no contexts found, generate new queries directly
            return await AsyncHelper.generate_search_queries_async(client, token_counter, user_query, 2, lang)
            
        context_combined = "\n".join([f"{context[:1000]} [...]" for context in all_contexts])
        prompt = Prompts.analytics(lang)
        messages = [
            {"role": "system", "content": "You are a systematic research planner." if lang == 'en' else "Vous êtes un planificateur de recherche systématique."},
            {"role": "user", "content": f"Contexte pertinent trouvé:\n{context_combined}\n\n Fin du contexte.\n{prompt}\nDemande utilisateur: {user_query}\nRecherches précédentes déjà effectuées: {previous_search_queries}"}
        ]
        response = await AsyncHelper.call_openrouter_async(client, token_counter, messages, max_tokens=100, step='ANALYTICS')
        if response:
            cleaned = response.strip()
            print("EVALUATOR:", cleaned)
            if "[]" in cleaned:
                print("Research complete")
                return "[]"
            try:
                new_queries = eval(cleaned)
                if isinstance(new_queries, list):
                    return new_queries
                else:
                    print("LLM did not return a list for new search queries. Response:", response)
                    return []
            except Exception as e:
                print("Error parsing new search queries:", e, "\nResponse:", response)
                return []
        return []

    @staticmethod
    async def generate_final_report_async(client, token_counter, user_query, all_contexts, urls, prompt_suffix, max_tokens, lang='fr', event_emitter=None):
        if not all_contexts:
            return "No relevant information found to answer your query.", ""
            
        if prompt_suffix:
            prompt_suffix = f"User instructions importantes: {prompt_suffix}" if lang == 'fr' else f"Important user instructions: {prompt_suffix}"
        else:
            prompt_suffix = ''
        context_combined = "\n".join(all_contexts)
        prompt = Prompts.redactor(lang)
        messages = [
            {"role": "system", "content": "You are a talented assistant." if lang == 'en' else "Vous êtes un assistant talentueux qui réponds en se basant sur les contexte rassemblés."},
            {"role": "user", "content": f"Contextes pertinents rassemblés:\n{context_combined}\nFin du contexte.\n URLs utilisées: {urls}\n\n{prompt}\n{prompt_suffix}\nFais très attention aux urls dans ta réponse, N'utilises que les urls qui sont dans le contexte rassemblé."}
        ]
        #report = await AsyncHelper.call_openrouter_async(client, token_counter, messages, max_tokens=max_tokens, step='END')
        
        #return report or "Failed to generate a report.", messages[1]["content"]
        return messages[-1]["content"], prompt

    @staticmethod
    async def process_link(client, token_counter, link, user_query, search_query, log, lang='fr', num_queries=2, event_emitter=None):
        log.append(f"Fetching content from: {link}")
        print("FETCHING CONTENT FROM: ", link)
        page_text = await AsyncHelper.fetch_webpage_text_async(link)
        if not page_text:
            print("FAILED TO FETCH CONTENT FROM: ", link)
            log.append(f"Failed to fetch content from: {link}")
            return ''
        usefulness = await AsyncHelper.is_page_useful_async(client, token_counter, user_query, page_text, lang)
        log.append(f"Page usefulness for {link}: {usefulness}")
        await emit_status(event_emitter, f"Je lis le contenu de {link}...")
        if usefulness == "Oui" and num_queries > 1:
            context = await AsyncHelper.extract_relevant_context_async(client, token_counter, user_query, search_query, page_text, link, lang=lang)
            if context:
                print(f"Extracted context from {link} (first 200 chars): {context[:200]}")
                log.append(f"Extracted context from {link} (first 200 chars): {context[:200]}")
                await emit_status(event_emitter, f"J'ai extrait le contenu pertinent de {link}...")
                return str([link]) + context
        elif num_queries == 1:
            print(f"Page text from {link} sent directly (simple search)")
            return str([link]) +page_text
        return ''

async def emit_status(event_emitter, description):
    await event_emitter(
        {
            "type": "status",
            "data": {"description": description, "done": False, "hidden": False},
        }
    )

async def async_research(client, user_query, internet, iteration_limit, prompt_suffix=None, max_tokens=1024, num_queries=2, k=5, lang='fr', collections=None, user=None, request=None, event_emitter=None):
    start_time = time.time()
    aggregated_contexts = []
    aggregated_chunks = []
    all_search_queries = []
    log_messages = []
    iteration = 0
    token_counter = TokenCounter()

    #await emit_status(event_emitter, "Je cherche dans le rag...")
    
    # Input validation
    if not user_query or not user_query.strip():
        return "Please provide a valid query.", "Error: Empty query", "", 0, 0, [], 0
    
    iteration_limit = max(1, min(iteration_limit, 10))  # Ensure between 1 and 10
    num_queries = max(1, min(num_queries, 5))  # Ensure between 1 and 5
    k = max(1, min(k, 10))  # Ensure between 1 and 10

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
            log_messages.append(f"Starting research for: {user_query}")
            log_messages.append("Generating initial search queries...")
            await emit_status(event_emitter, "J'évalue la demande...")
            
            new_search_queries = await AsyncHelper.generate_search_queries_async(client, token_counter, user_query, num_queries, lang)
            
            if not new_search_queries:
                log_messages.append("No search queries were generated. Using the original query.")
                new_search_queries = [user_query]
                
            all_search_queries.extend(new_search_queries)
            log_messages.append(f"Initial search queries: {new_search_queries}")
            print(f"Initial search queries: {new_search_queries}")
            await emit_status(event_emitter, f"Je cherche {', '.join(new_search_queries)}...")

            while iteration < iteration_limit:
                log_messages.append(f"\n=== Iteration {iteration + 1} ===")
                iteration_contexts = []
                all_links = []
                
                if internet:
                    await emit_status(event_emitter, "Je me connecte à internet...")
                    print("LAUNCHING INTERNET SEARCH")
                    search_results = []
                    for query in new_search_queries[:num_queries]:
                        search_results.append(await AsyncHelper.perform_brave_search_async(client, query, k, num_queries))
                    
                    unique_links = {}
                    for idx, links in enumerate(search_results):
                        query_used = new_search_queries[idx]
                        for link in links:
                            if link not in unique_links:
                                unique_links[link] = query_used
                                all_links.append(link)
                    log_messages.append(f"Found {len(unique_links)} unique links in iteration {iteration + 1}.")
                    
                    if not unique_links:
                        print("No links found in this iteration.")
                        log_messages.append("No links found in this iteration.")
                    else:
                        print("Processing links...")
                        link_tasks = [
                            AsyncHelper.process_link(client, token_counter, link, user_query, unique_links[link], log_messages, lang, num_queries, event_emitter)
                            for link in unique_links
                        ]
                        link_results = await asyncio.gather(*link_tasks)
                        iteration_contexts = [res for res in link_results if res]
                        aggregated_chunks.extend([link for link in unique_links])
                else:
                    print("LAUNCHING RAG SEARCH")
                    if num_queries > 1:
                        await emit_status(event_emitter, "Je lance une recherche approndie dans les bases de connaissances disponibles...")
                    else:
                        await emit_status(event_emitter, "Je lance une recherche dans les bases de connaissances disponibles...")
                    search_api_tasks = [AsyncHelper.process_query_api(client, token_counter, user_query, search, k, log_messages, lang, collections, user, request) for search in new_search_queries[:num_queries]]
                    useful_docs_lists = await asyncio.gather(*search_api_tasks)
                    
                    # Flatten and deduplicate
                    useful_docs = []
                    seen = set()
                    for doc_list in useful_docs_lists:
                        for doc in doc_list:
                            # Use a hash of the first 100 chars as a deduplication key
                            doc_hash = hash(doc[:100])
                            if doc_hash not in seen:
                                seen.add(doc_hash)
                                useful_docs.append(doc)
                    
                    print(f"Useful docs after deduplication: {len(useful_docs)}")

                    await emit_status(event_emitter, f"J'ai trouvé {len(useful_docs)} documents pertinents...")
                    
                    if useful_docs and num_queries > 1: # if we have more than one query it's complex, we need to process the docs
                        iteration_contexts = await AsyncHelper.process_useful_api_docs(client, token_counter, user_query, useful_docs, log_messages, lang)
                        aggregated_chunks.extend(useful_docs)
                    else:
                        iteration_contexts = useful_docs
                        aggregated_chunks.extend(useful_docs)

                    await emit_status(event_emitter, "J'ai fini de lire les documents pertinents...")

                if iteration_contexts:
                    aggregated_contexts.extend(iteration_contexts)
                    print(f"Found {len(iteration_contexts)} useful contexts in iteration {iteration + 1}.")
                    log_messages.append(f"Found {len(iteration_contexts)} useful contexts in iteration {iteration + 1}.")
                else:
                    print(f"No useful contexts found in iteration {iteration + 1}.")
                    log_messages.append(f"No useful contexts found in iteration {iteration + 1}.")

                if iteration_limit > 1:    
                    new_search_queries = await AsyncHelper.get_new_search_queries_async(client, token_counter, user_query, all_search_queries, aggregated_contexts, lang)
                else:
                    new_search_queries = []

                if new_search_queries == "[]":
                    log_messages.append("LLM indicated that no further research is needed or iteration limit reached.")
                    break
                elif new_search_queries:
                    log_messages.append(f"New search queries for iteration {iteration + 2}: {new_search_queries}")
                    all_search_queries.extend(new_search_queries)
                else:
                    log_messages.append("No new search queries provided. Ending research.")
                    break

                iteration += 1

            log_messages.append("\nGenerating final report...")
            await emit_status(event_emitter, "Les recherches sont terminées ! Je résume les informations que j'ai trouvé...")

            if num_queries > 1:
                final_report, final_prompt = await AsyncHelper.generate_final_report_async(
                    client, token_counter, user_query, aggregated_contexts, all_links, prompt_suffix, max_tokens, lang, event_emitter
                )
            else:
                final_report, final_prompt = str(aggregated_contexts) + "\n Voilà les documents que j'ai trouvé pour ta recherche, utilises ces informations pour répondre à la question de l'utilisateur. Donnes les sources et liens intéressants si il y en a. CETTE REPONSE N'EST PAS COMPLETE, TU DOIS REDIGER LA REPONSE.", ""
            
            total_input_tokens, total_output_tokens = await token_counter.get_totals()
            elapsed_time = time.time() - start_time
            
            log_messages.append(f"\nResearch completed in {elapsed_time:.2f} seconds.")
            log_messages.append(f"Total input tokens: {total_input_tokens}")
            log_messages.append(f"Total output tokens: {total_output_tokens}")

            # Citation for the front
            if event_emitter:
                n_source = 0
                for chunk in aggregated_chunks:
                    n_source+=1
                    if internet:
                        name = chunk
                    else:
                        name = f"Source {n_source}"
                    await event_emitter(
                {
                    "type": "citation",
                    "data": {
                        "document": [chunk],
                        "metadata": [{"source": f"[Source {n_source}]({extract_first_url(chunk)})"}],
                        "source": {"name": name},
                    },
                }
            )

            return final_report, "\n".join(log_messages), final_prompt, total_input_tokens, total_output_tokens, aggregated_chunks, elapsed_time
            
    except Exception as e:
        error_msg = f"Error during research: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return f"An error occurred: {str(e)}", error_msg, "", 0, 0, [], time.time() - start_time

def run_research(client, user_query, internet, iteration_limit=10, prompt_suffix='', max_tokens=2048, num_queries=2, k=5, lang='fr', collections=None, user=None, request=None, event_emitter=None):
    # Wrapper to run the async_research safely in a new thread.
    result_container = {}

    def _run():
        # Create a new event loop for this thread and run the coroutine.
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            result_container['result'] = loop.run_until_complete(
                async_research(client, user_query, internet, iteration_limit, prompt_suffix, max_tokens, num_queries, k, lang, collections, user, request, event_emitter)
            )
        finally:
            loop.close()

    thread = threading.Thread(target=_run)
    thread.start()
    thread.join()
    return result_container.get('result')