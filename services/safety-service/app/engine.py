"""Défense locale en dix couches. Aucun appel de modèle cloud ni journal de texte brut."""
import base64
from collections import Counter
from dataclasses import dataclass
import html
import re
from threading import Lock
import unicodedata
from urllib.parse import unquote
from uuid import uuid4

from .schemas import AnalyzeResponse, LayerResult

NAMES = ["resource_and_encoding", "instruction_override", "role_impersonation",
    "personal_data_exfiltration", "tool_and_code_execution", "sexual_content",
    "dangerous_instructions", "distress_and_self_harm", "hate_and_harassment", "pii_and_output_gate"]

RULES = {
    2: [r"\b(ignore|oublie|ignorer|contourne|bypass|disregard)\b.{0,90}\b(instruction|consigne|regle|rule|previous|precedent|securite|safety)",
        r"\b(?:ne respecte pas|sans respecter)\b.{0,45}\b(?:regles?|consignes?|instructions?)\b",
        r"\b(revele|affiche|donne|reveal|show|print)\b.{0,50}\b(prompt systeme|system prompt|instructions internes)\b"],
    3: [r"<\|(?:im_start|system|assistant|developer|im_end)\|>", r"\[/?(?:INST|SYSTEM)\]",
        r"\b(?:system|developer|assistant)\s*:", r"\b(?:tu es maintenant|act as|mode)\b.{0,40}\b(?:dan|sans restriction|unrestricted|developpeur|jailbreak)\b"],
    4: [r"\b(?:donne|liste|affiche|revele|envoie|trouve|show|reveal|list|send|find)\b.{0,70}\b(?:emails?|e-mails?|adresses?|mots? de passe|passwords?|coordonnees|noms? de famille|nom des eleves|nom de l.eleve|prenoms? des eleves)\b",
        r"\b(?:quel|quelle|quels|quelles|what|where)\b.{0,60}\b(?:emails?|adresses?|coordonnees|nom de famille|mots? de passe|passwords?|home address|last name)\b",
        r"\b(?:exfiltre|exfiltrate|steal|vole)\b.{0,60}\b(?:donnees|data|tokens?|secrets?)\b"],
    5: [r"\b(?:exec|eval|os\.system|subprocess|__import__)\s*\(", r"<script\b|javascript\s*:",
        r"\b(?:execute|executer|lance|run|appelle)\b.{0,60}\b(?:commande|shell|powershell|curl|wget|outil|function|tool)\b",
        r"\b(?:curl|wget)\s+https?://", r"\b(?:drop|truncate)\s+table\b"],
    6: [r"\b(?:porno\w*|pornograph\w*|porn|nudes?|sexe explicite|sexual explicit|masturb\w*|fellati\w*|penetration sexuelle)\b",
        r"\b(?:envoie|montre|send|show)\b.{0,40}\b(?:photo nue|photos nues|tes parties intimes|naked|nude)\b",
        r"\b(?:notre secret|ne le dis pas a tes parents)\b.{0,60}\b(?:photo|corps|caresse|nu[es]?|rendez.vous)\b"],
    7: [r"\b(?:comment|apprends|explique|fabrique|fabriquer|construire|build|make|how to|recette)\b.{0,80}\b(?:bombe|explosif|arme a feu|poison|molotov|drogue|methamphetamine)\b",
        r"\b(?:tuer|empoisonner|egorger|kill|stab)\b.{0,40}\b(?:quelqu.un|camarade|prof|ami|person|teacher)\b"],
    8: [r"\b(?:je veux mourir|je veux disparaitre|me suicider|me faire du mal|i want to die|kill myself|suicide|automutilation)\b",
        r"\b(?:on me harcele|on me frappe|on me menace|je suis harcele|un adulte me touche|i am being bullied)\b"],
    9: [r"\b(?:sale|sales|tous les|toutes les)\b.{0,25}\b(?:noirs?|arabes?|juifs?|musulmans?|homosexuels?)\b.{0,35}\b(?:dehors|inferieurs?|meritent|deteste|tuer|morts?)\b",
        r"\b(?:harcele|harceler|humilie|humilier|insulte|insulter|bully|humiliate)\b.{0,40}\b(?:eleve|camarade|fille|garcon|classmate)\b",
        r"\b(?:sale con|ta gueule|connard|connasse|salope|negres?)\b"],
}
PATTERNS = {layer: [re.compile(pattern, re.I | re.S) for pattern in patterns] for layer, patterns in RULES.items()}


def folded(text):
    text = text.translate(str.maketrans({"а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "х": "x", "і": "i", "ј": "j"}))
    return "".join(c for c in unicodedata.normalize("NFKD", text).lower() if not unicodedata.combining(c))


def normalize(text):
    result = unicodedata.normalize("NFKC", text)
    for _ in range(2):
        result = html.unescape(unquote(result))
    return "".join(c for c in result if c not in "\u200b\u200c\u200d\ufeff\u00ad")


@dataclass(frozen=True)
class Span:
    start: int
    end: int
    category: str


PII_PATTERNS = {
    "EMAIL": re.compile(r"\b[A-Z0-9._%+-]+\s*(?:@|\[(?:at|arobase)\]|\((?:at|arobase)\)|\barobase\b)\s*[A-Z0-9.-]+\s*(?:\.|\[(?:dot|point)\]|\bpoint\b)\s*[A-Z]{2,}\b", re.I),
    "PHONE": re.compile(r"(?<!\w)(?:(?:\+33|0033)\s*\(?0?\)?\s*[1-9]|0[1-9])(?:[ .-]?\d{2}){4}(?!\d)"),
    "ADDRESS": re.compile(r"\b\d{1,4}\s*(?:bis|ter)?\s+(?:rue|avenue|av\.?|boulevard|bd\.?|impasse|chemin|allee|allée|place|route|street|road)\s+[\w'’ -]{2,90}", re.I),
    "SCHOOL_ID": re.compile(r"\b(?i:ecole|école|college|collège|lycee|lycée|school)\s+(?:(?:primaire|elementaire|élémentaire|publique|privee|privée)\s+)?[A-ZÀ-ÖØ-Ý][\w'’-]*(?:\s+(?:de|du|des|la|le|[A-ZÀ-ÖØ-Ý][\w'’-]*)){0,5}"),
    "IDENTIFIER": re.compile(r"\b(?:sk[-_][A-Za-z0-9_-]{16,}|eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)\b"),
    "URL": re.compile(r"(?:https?://|www\.)[^\s<>]+", re.I),
}
INTRO = re.compile(r"\b(?:je m.appelle|mon (?:nom|prenom|prénom) est|my name is)\s+([\w'’-]+(?:\s+(?!(?:et|je|j|etudiant|eleve|élève|and|i|de|dans)\b)[\w'’-]+){0,2})", re.I)
OPAQUE = re.compile(r"(?<!\w)[A-Za-z0-9+/]{40,}={0,2}(?!\w)")


class SafetyEngine:
    def __init__(self, model="fr_core_news_sm"):
        import spacy
        self.nlp = spacy.load(model, exclude=["parser", "lemmatizer", "attribute_ruler", "morphologizer"])
        if "ner" not in self.nlp.pipe_names:
            raise RuntimeError("NER component required")
        self.nlp.max_length = 12000
        self.lock = Lock()

    def spans(self, text, names=(), school_names=()):
        spans = [Span(match.start(), match.end(), category) for category, pattern in PII_PATTERNS.items() for match in pattern.finditer(text)]
        spans.extend(Span(m.start(1), m.end(1), "STUDENT_ID") for m in INTRO.finditer(text))
        # Indices conservés même si un caractère se décompose lors de la comparaison sans accents.
        chars, indexes = [], []
        for index, char in enumerate(text):
            for unit in folded(char):
                chars.append(unit)
                indexes.append(index)
        comparable = "".join(chars)
        for words, category in [(names, "STUDENT_ID"), (school_names, "SCHOOL_ID")]:
            for value in words:
                value = folded(value.strip())
                if len(value) < 2:
                    continue
                for match in re.finditer(r"(?<!\w)" + re.escape(value) + r"(?!\w)", comparable):
                    spans.append(Span(indexes[match.start()], indexes[match.end()-1] + 1, category))
        with self.lock:
            entities = [(e.start_char, e.end_char, e.label_) for e in self.nlp(text).ents]
        for start, end, label in entities:
            if start == 0 and folded(text[start:end]) in {"combien", "pourquoi", "comment", "quand", "quel", "quelle"}:
                # Correction limitée des interrogatifs initiaux ; les identités connues restent masquées.
                continue
            if label in {"PER", "LOC", "ORG"}:
                category = {"PER": "STUDENT_ID", "LOC": "ADDRESS", "ORG": "ORGANIZATION"}[label]
                spans.append(Span(start, end, category))
        return spans

    def redact(self, text, names=(), school_names=()):
        spans = sorted(self.spans(text, names, school_names), key=lambda s: (s.start, -s.end))
        merged = []
        for span in spans:
            if merged and span.start < merged[-1].end:
                previous = merged[-1]
                # Une adresse complète prime sur le nom propre reconnu à l'intérieur.
                merged[-1] = Span(previous.start, max(previous.end, span.end), previous.category)
            else:
                merged.append(span)
        counts = Counter(span.category for span in merged)
        result = text
        for span in reversed(merged):
            result = result[:span.start] + f"[{span.category}]" + result[span.end:]
        return result, dict(counts)

    def analyze(self, raw, names=(), school_names=()):
        text = normalize(raw)
        resource_codes = []
        if not text.strip() or len(raw) > 6000 or len(raw.encode()) > 24000 or len(text) > 6000:
            resource_codes.append("input_limit")
        if any((ord(c) < 32 and c not in "\n\r\t") or c in "\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069" for c in raw):
            resource_codes.append("unicode_control")
        for match in OPAQUE.finditer(text):
            try:
                decoded = base64.b64decode(match.group(), validate=True).decode("utf-8")
                if decoded and sum(c.isprintable() or c.isspace() for c in decoded) / len(decoded) > .9:
                    resource_codes.append("encoded_payload")
            except (ValueError, UnicodeError):
                continue
        layers = [LayerResult(layer=1, name=NAMES[0], status="block" if resource_codes else "pass", codes=resource_codes)]
        view = folded(text[:6000])
        compact = re.sub(r"\b(?:[a-z]\s+){3,}[a-z]\b", lambda m: re.sub(r"\s+", "", m.group()), view)
        views = [view, compact, compact.translate(str.maketrans("013457", "oieast"))]
        for layer in range(2, 10):
            blocked = any(pattern.search(v) for pattern in PATTERNS[layer] for v in views)
            layers.append(LayerResult(layer=layer, name=NAMES[layer-1], status="block" if blocked else "pass", codes=[NAMES[layer-1]] if blocked else []))
        sanitized, counts = None, {}
        if resource_codes:
            layers.append(LayerResult(layer=10, name=NAMES[9], status="not_run", codes=["resource_guard"]))
        else:
            sanitized, counts = self.redact(text, names, school_names)
            # Vérification résiduelle des identifiants structurés, sans reclassifier les marqueurs anonymes.
            residual = any(pattern.search(sanitized) for pattern in PII_PATTERNS.values())
            layers.append(LayerResult(layer=10, name=NAMES[9], status="block" if residual else ("redact" if counts else "pass"), codes=["residual_pii"] if residual else sorted(counts)))
        blocked = any(layer.status == "block" for layer in layers)
        support = layers[7].status == "block"
        message = ("Tu as bien fait d'en parler. Va voir un adulte de confiance maintenant. Si tu es en danger immédiat, demande de l'aide tout de suite." if support
            else "Je ne peux pas transmettre ce message. Tu peux demander de l'aide à un adulte ou reformuler ta question." if blocked else None)
        return AnalyzeResponse(request_id=uuid4(), decision="block" if blocked else ("redact" if counts else "allow"),
            sanitized_text=None if blocked else sanitized, layers=layers, redactions=counts,
            requires_adult_support=support, message=message)
