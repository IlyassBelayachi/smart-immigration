"""Entretien d'orientation local, sans service externe."""
import re
import unicodedata

from .recommend import suggest

QUESTIONS = (
    ("projet", "Parlez-moi de votre projet. Que voulez-vous faire à l’étranger et dans quel délai ?"),
    ("parcours", "Quel est votre parcours ? Décrivez vos études, votre métier et votre expérience."),
    ("langues", "Quelles langues parlez-vous et dans laquelle voulez-vous travailler ou étudier ? Pourriez-vous en apprendre une autre ?"),
    ("budget", "Quel budget avez-vous prévu, dans quelle devise, et sur quelles ressources comptez-vous ? Si vous ne savez pas encore, dites-le."),
    ("famille", "Avec qui comptez-vous partir ? Quelles contraintes de logement, de scolarité ou d’accompagnement dois-je connaître ?"),
    ("priorites", "Quelles régions envisagez-vous ou excluez-vous ? Avez-vous des contacts sur place ? Dites-moi aussi ce qui pourrait vous faire renoncer à une destination."),
)

MOTIVE_WORDS = {
    "study": r"etud|universit|master|licence|doctorat",
    "family": r"rejoindre|regroupement",
    "entrepreneur": r"entrepren|creer une entreprise",
    "work": r"travail|emploi|job|salar",
    "visit": r"touris|visit",
}

LANGUAGES = {"francais": "fr", "anglais": "en", "espagnol": "es", "allemand": "de",
             "italien": "it", "neerlandais": "nl", "turc": "tr", "hebreu": "he"}
PLACES = {"canada": "CA", "france": "FR", "espagne": "ES", "italie": "IT", "belgique": "BE",
          "allemagne": "DE", "pays-bas": "NL", "suisse": "CH", "turquie": "TR", "israel": "IL"}


def normalize(value: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", value.lower()) if not unicodedata.combining(c))


def project_motive(project: str) -> str:
    text = normalize(project)
    return next((key for key, pattern in MOTIVE_WORDS.items() if re.search(pattern, text)), "other")


def next_question(topic: str, transcript: dict) -> str:
    default = dict(QUESTIONS)[topic]
    if topic == "parcours":
        return {
            "work": "Pour mieux comprendre votre projet de travail, quel métier exercez-vous, depuis combien de temps et avec quelles qualifications ?",
            "study": "Pour mieux comprendre votre projet d’études, quelles études avez-vous déjà suivies, et quel domaine ou programme visez-vous ?",
            "family": "Quel proche souhaitez-vous rejoindre, et dans quel pays vit-il actuellement ? Vous pouvez aussi préciser votre situation professionnelle.",
            "entrepreneur": "Quelle activité souhaitez-vous lancer et quelle expérience avez-vous dans ce domaine ?",
        }.get(project_motive(transcript["projet"]), default)
    return default


def clarification(topic: str, answer: str) -> str | None:
    text = normalize(answer)
    if topic in {"projet", "parcours", "famille", "priorites"} and len(text.split()) < 2:
        return "Pouvez-vous développer en quelques mots ?"
    if topic == "budget":
        uncertain = re.search(r"\b(inconnu|aucun|imprecis|estimer|definir|sais pas|pas encore)\b", text)
        amount = re.search(r"\d", text)
        currency = re.search(r"\b(mad|eur|cad|usd|dh|dirhams?|euros?|dollars?)\b|[€$]", text)
        if amount and not currency:
            return "Dans quelle devise est ce montant ? Réécrivez le budget avec le montant et sa devise."
        if not amount and not uncertain:
            return "Pouvez-vous donner un montant et sa devise, ou préciser que le budget reste à définir ?"
    return None


TOPIC_LABELS = {
    "projet": "Projet", "parcours": "Parcours", "langues": "Langues",
    "budget": "Budget", "famille": "Installation", "priorites": "Priorités",
}
NEAR_MOROCCO = r"pas (?:tres )?(?:loin|eloigne) du maroc|proch\w* du maroc|pres du maroc"
UNKNOWN = r"je (?:ne )?sais pas|aucune idee|pas encore|a definir|je n.ai (?:plus|pas) d.info"
STOP = r"(?:plus rien|plus d.info|rien d.autre|autres informations je ne l.ai pas|aucune autre info|rien a ajouter|(?:les )?seules? (?:informations?|infos?) (?:que )?j.ai|c.est tout(?: ce que je sais)?)"


def collect(text: str) -> tuple[dict, dict]:
    regions = {"europe": "europe", "amerique": "america", "asie": "asia"}
    languages = [code for word, code in LANGUAGES.items()
                 if re.search(r"\b" + word + r"\b", text)
                 and not re.search(r"ne parle pas (?:le |l.)?" + word, text)]
    region = next((code for word, code in regions.items() if re.search(r"\b" + word + r"\b", text)), "")
    near = bool(re.search(NEAR_MOROCCO, text))
    exclusions = [code for word, code in PLACES.items()
                  if re.search(r"\b(?:sauf|evite[r]?|exclu\w*|pas de|pas en|pas au)\s+(?:(?:la|le|les) )?" + word + r"\b", text)]
    contact = re.search(r"\b(?:j.ai|j.y ai|j.y connais)\b.{0,35}\b(?:ami\w*|famille|proche|contact|employeur)\b([^.!?;]*)", text)
    contact_code = next((code for word, code in PLACES.items() if contact and word in contact[0]), "")
    facts = {}
    if languages:
        facts["langues"] = ", ".join(word.capitalize() for word, code in LANGUAGES.items() if code in languages)
    if near or region or exclusions or contact_code:
        facts["priorites"] = " · ".join(filter(None, [
            "Proche du Maroc" if near else "",
            next((word.capitalize() for word, code in regions.items() if code == region), ""),
            "Destinations exclues : " + ", ".join(word.capitalize() for word, code in PLACES.items() if code in exclusions) if exclusions else "",
            "Contact : " + next(word.capitalize() for word, code in PLACES.items() if code == contact_code) if contact_code else "",
        ]))
    if re.search(r"\b(?:ingenierie|inge|informatique|developpeur|licence|baccalaureat|master)\b", text):
        facts["parcours"] = "Domaine ou parcours évoqué"
    if re.search(r"\d[\d .,]*\s*(?:mad|eur|cad|usd|dh|dirhams?|euros?|dollars?|[€$])", text):
        facts["budget"] = "Montant avec devise indiqué"
    if re.search(r"je par[st] (?:seul\w*|avec)|mes enfants m.accompagnent", text):
        facts["famille"] = "Situation d’accompagnement indiquée"
    return facts, {"languages": languages, "region": region, "near_morocco": near, "excluded": exclusions,
                   "contact": contact_code, "adapt": "no" if re.search(r"(?:pas|impossible).{0,25}apprendre", text) else ""}


def interview(answers: list[str], confirmed: bool = False) -> dict:
    transcript = {}
    messages = []
    facts = {}
    preferences = {}
    remaining = list(TOPIC_LABELS)
    for answer in answers:
        if not remaining:
            break
        topic = remaining[0]
        answer = answer.strip()
        normalized = normalize(answer)
        unknown = bool(re.search(UNKNOWN, normalized))
        stop = bool(re.search(STOP, normalized))
        if not unknown and not stop:
            followup = clarification(topic, answer)
            if followup:
                return {"question": followup, "accepted": len(messages)}
            if not answer or not any(char.isalpha() for char in answer):
                return {"question": next_question(topic, transcript), "accepted": len(messages)}
        transcript[topic] = answer
        messages.append(normalized)
        facts, preferences = collect(". ".join(messages))
        remaining = [key for key in TOPIC_LABELS if key not in transcript and key not in facts]
        if stop:
            for key in remaining:
                transcript[key] = "Non renseigné"
            remaining = []

    summary = {TOPIC_LABELS[key]: facts.get(key, transcript.get(key)) for key in TOPIC_LABELS
               if key in facts or key in transcript}
    if remaining:
        recognized = [facts[key] for key in ("langues", "priorites") if key in facts]
        acknowledgment = f"J’ai retenu : {' · '.join(recognized)}. " if recognized else ""
        return {"question": acknowledgment + next_question(remaining[0], transcript), "accepted": len(messages)}
    if not confirmed:
        return {"question": "Voici ce que j’ai retenu. Confirmez le récapitulatif pour voir les pistes.",
                "accepted": len(messages), "ready": True, "summary": summary}
    return {"accepted": len(messages), "suggestions": suggest(preferences), "preferences": preferences,
            "summary": summary, "motive": project_motive(transcript["projet"]), "transcript": transcript}
