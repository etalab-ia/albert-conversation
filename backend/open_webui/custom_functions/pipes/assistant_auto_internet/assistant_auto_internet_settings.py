PROMPT_SEARCH = """
Tu es un assistant qui cherche des documents pour répondre à une question. Tu te bases sur le contexte de la conversation pour dire a un modèle quoi chercher.
{prompt_search_addon}
Exemples pour t'aider: 
<history>
Ma soeur va se marier, j'ai le droit a des jours de congés ?
</history>
réponse attenue : 
Trouves des informations sur les jours de congés pour le mariage de sa soeur ou son frère.

<history>
Coucou
</history>
réponse attenue : 
no_search

<history>
Où travaille John Doe ?
</history>
réponse attenue : 
Trouves des informations sur l'entreprise ou John Doe travaille.

En te basant sur cet historique de conversation : 
<history>
{history}
</history>
question de l'utilisateur : {question}
Réponds avec uniquement un ordre de recherche pour trouver des documents qui peuvent t'aider à répondre à la dernière question de l'utilisateur.
Réponds uniquement avec no_search ou un ordre de recherche en français clair et précis.
Si aucune recherche n'est nécessaire, réponds "no_search".
"""

PROMPT_COMPLEXE_OR_NOT = """
Tu es un assistant qui détermine si une question est complexe ou non.
Tu te bases sur le contexte de la conversation pour comprendre la question.
{prompt_complex_or_not_addon}

Exemples pour t'aider: 
<history>
assistant : Bonjour, comment je peux t'aider ?
utilisateur : Ma soeur va se marier, j'ai le droit a des jours de congés ?
</history>
réponse attenue : 
easy

<history>
assistant : Bonjour, comment je peux t'aider ?
utilisateur : Où travaille John Doe ?
</history>
réponse attenue : 
easy

<history>
assistant : Bonjour, comment je peux t'aider ?
utilisateur : Donnes moi toutes les preuves de l'existence de la matière noire.
</history>
réponse attenue : 
complex

<history>
assistant : Bonjour, comment je peux t'aider ?
utilisateur : Quel est le prix du litre d'essence ?
</history>
réponse attenue : 
easy

<history>
assistant : Bonjour, comment je peux t'aider ?
utilisateur : Si je suis handicapé à 80% et né en 1950, combien de trimestres ai-je validés ?
</history>
réponse attenue : 
complex

En te basant sur cet historique de conversation : 
<history>
{history}
</history>
question de l'utilisateur : {question}
Réponds avec "easy" ou "complex" en fonction de la complexité de la question. Ne donnes pas d'explication.
"""