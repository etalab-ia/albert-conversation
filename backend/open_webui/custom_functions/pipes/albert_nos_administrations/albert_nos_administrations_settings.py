collection_dict = {
    "annuaire-administrations-etat": 783,
}


SYSTEM_PROMPT = """
Tu es Albert, un assistant développé par l'Etalab qui répond à des questions en te basant sur un contexte.
Tu parles en français. Tu es précis et poli.
Tu es connecté aux collections suivantes : {collections} sur AlbertAPI.
Ce que tu sais faire : Tu sais répondre aux questions et chercher dans les bases de connaissance de Albert API qui concerne les administrations publiques.
Pour les questions sur des sujets spécifiques autres que les administrations publiques, invites l'utilisateur à se tourner vers un autre assistant spécialisé.
Ne donnes pas de sources si tu réponds à une question meta ou sur toi.
"""

PROMPT = """
<context trouvé dans la base>
{context}
</context trouvé dans la base>

En t'aidant si besoin du le contexte ci-dessus, réponds à cette question :
<question>
{question}
</question>

Réponds uniquement à la question de manière claire. Dans ces questions, l'utilisateur peut se tromper de genre.
A la fin de ta réponse, ajoute les sources ou liens urls utilisés pour répondre à la question. Quand tu mets des liens donne leurs des noms simples avec la notation markdown.
Si tu mets des sources en fin de réponse, ne mets QUE les sources liées à ta réponse, jamais de source inutilement.
Si tu ne trouves pas d'éléments de réponse dans le contexte ou dans ton prompt system, réponds que tu manques d'informations ou demande des précisions ou demande comment tu peux aider. Sois poli.
"""

PROMPT_SEARCH_ADDON = """
Tu peux chercher des informations sur les administrations publiques ou les personnes y travaillant en utilisant les mots clés suivants :
- nom et prénom de la personne
- nom de l'administration
- code postal
- ville
- pays
Pour une recherche sur une personne, tu peux répondre avec uniquement le nom et prénom.
"""

def format_chunks_to_text(chunk: dict) -> str:
    adresses_to_concatenate = []
    try:
        for adresse in chunk.get("addresses", [{}]):
            if adresse.get("adresse", ""):
                adresses_to_concatenate.append(
                    f"{adresse.get('adresse', '')}, {adresse.get('code_postal', '')} {adresse.get('commune', '')} {adresse.get('pays', '')}".strip()
                )
            else:
                adresses_to_concatenate.append(
                    f"{adresse.get('code_postal', '')} {adresse.get('commune', '')} {adresse.get('pays', '')}".strip()
                )

        # Concatenate all addresses in order to add them to the data to embed
        adresses_to_concatenate = ".\n".join(adresses_to_concatenate)
        adresses_to_concatenate = (
            "Adresses :\n" + adresses_to_concatenate if adresses_to_concatenate else ""
        )
    except Exception:
        pass

    emails_to_concatenate = []
    try:
        for email in chunk.get("mails", []):
            emails_to_concatenate.append(email)
        # Concatenate all emails in order to add them to the data to embed
        emails_to_concatenate = ".\n ".join(emails_to_concatenate)
        emails_to_concatenate = (
            "Emails :\n" + emails_to_concatenate if emails_to_concatenate else ""
        )
    except Exception:
        pass

    phone_numbers_to_concatenate = []
    try:
        for phone_number in chunk.get("phone_numbers", [{}]):
            phone_numbers_to_concatenate.append(phone_number)
        # Concatenate all phone numbers in order to add them to the data to embed
        phone_numbers_to_concatenate = ".\n".join(phone_numbers_to_concatenate)
        phone_numbers_to_concatenate = (
            "Téléphones :\n" + phone_numbers_to_concatenate
            if phone_numbers_to_concatenate
            else ""
        )
    except Exception:
        pass

    urls_to_concatenate = []
    try:
        for url in chunk.get("urls", []):
            urls_to_concatenate.append(url)
        # Concatenate all urls in order to add them to the data to embed
        urls_to_concatenate = "\n".join(urls_to_concatenate)
        urls_to_concatenate = (
            "URLs :\n" + urls_to_concatenate if urls_to_concatenate else ""
        )
    except Exception:
        pass

    responsables_to_concatenate = []
    try:
        for k, responsable in enumerate(chunk.get("people_in_charge", "")):
            resp = f"Personne {k + 1} : {responsable.get('fonction', '')}"
            if responsable.get("personne", {}):
                personne = responsable.get("personne", {})
                resp += f" : {personne.get('civilite', '')} {personne.get('prenom', '')} {personne.get('nom', '')}"
                if personne.get("grade", ""):
                    resp += f" ({personne.get('grade', '')})"
                if personne.get("adresse_courriel", []):
                    for mail in personne.get("adresse_courriel", []):
                        resp += f"\nEmail : {mail.get('valeur', '')} ({mail.get('libelle', '')})"
            if responsable.get("telephone", ""):
                resp += f"\nTéléphone : {responsable.get('telephone', '')}"
            responsables_to_concatenate.append(resp)
        responsables_to_concatenate = ".\n".join(responsables_to_concatenate)
        responsables_to_concatenate = (
            "Responsables :\n" + responsables_to_concatenate
            if responsables_to_concatenate
            else ""
        )
    except Exception:
        pass

    directory_url = (
        f"URL de l'annuaire : {chunk.get('directory_url', 'NON DISPONIBLE')}"
    )

    # Text to embed in order to makes the search more efficient
    fields = [
        f"Nom : {chunk.get('name')}",
        f"Mission : {chunk.get('mission_description', '')}",
        # chunk.get("types", ""),
        adresses_to_concatenate if adresses_to_concatenate else "",
        phone_numbers_to_concatenate if phone_numbers_to_concatenate else "",
        emails_to_concatenate if emails_to_concatenate else "",
        urls_to_concatenate if urls_to_concatenate else "",
        responsables_to_concatenate if responsables_to_concatenate else "",
        directory_url if directory_url else "",
    ]
    final_text = ".\n".join([f for f in fields if f]).strip()

    return final_text