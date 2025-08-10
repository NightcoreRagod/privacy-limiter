import os, re, hashlib, json
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Tuple
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import openai, spacy
from textblob import TextBlob

# ---------- Engines ---------------------------------------------------------

class PIIMasker:
    PATTERNS = {                              # ── regex primitives
        "email":        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        "phone":        r"\b(?:\+?1[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}\b",
        "ssn":          r"\b\d{3}-?\d{2}-?\d{4}\b",
        "credit_card":  r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5]\d{14})\b",
        "ip":           r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
        "name":         r"\b[A-Z][a-z]+ [A-Z][a-z]+\b",
        "address":      r"\d+\s+[A-Za-z0-9\s,]+(?:St|Street|Rd|Road|Ave|Avenue)\b",
    }
    LEVELS = {                               # ── colour spectrum
        "public":       ("#28a745", 1),
        "internal":     ("#ffc107", 2),
        "confidential": ("#fd7e14", 3),
        "restricted":   ("#dc3545", 4),
    }
    def _init_(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            self.nlp = None

    # Detect
    def detect(self, text: str) -> Dict[str, List[dict]]:
        out = defaultdict(list)
        for k, pat in self.PATTERNS.items():
            for m in re.finditer(pat, text):
                out[k].append({"text": m.group(), "start": m.start(), "end": m.end(),
                               "sens": self._lvl(k)})
        if self.nlp:
            for ent in self.nlp(text).ents:
                if ent.label_ in {"PERSON","ORG","GPE"}:
                    out["entities"].append({"text": ent.text,
                                            "start": ent.start_char,
                                            "end": ent.end_char,
                                            "sens": "internal"})
        return out

    # Mask
    def mask(self, text:str) -> Tuple[str,Dict]:
        det = self.detect(text)
        flat = [d|{"type":k} for k,v in det.items() for d in v]
        flat.sort(key=lambda x: x["start"], reverse=True)
        mapping, out = {}, text
        for d in flat:
            mask = f"[MASKED_{d['type'].upper()}]"
            mapping[mask] = d["text"]
            out = out[:d["start"]] + mask + out[d["end"]:]
        return out, mapping

    # Colour-code
    def colour(self, text:str) -> str:
        det = self.detect(text)
        flat = [d for v in det.values() for d in v]
        flat.sort(key=lambda x:x["start"], reverse=True)
        out = text
        for d in flat:
            colour = self.LEVELS[d["sens"]][0]
            span = (f'<span style="background:{colour};color:#fff;'
                    f'padding:2px 4px;border-radius:3px;">{d["text"]}</span>')
            out = out[:d["start"]] + span + out[d["end"]:]
        return out

    def _lvl(self,k):               # simple mapping → level key
        if k in {"ssn","credit_card"}:         return "restricted"
        if k in {"email","phone","address"}:   return "confidential"
        return "internal"

class Corrector:
    def fix(self,text:str):
        blob = TextBlob(text)
        corrected = str(blob.correct())
        diff = [{"orig":o,"corr":c,"pos":i}
                for i,(o,c) in enumerate(zip(text.split(),corrected.split())) if o!=c]
        return corrected, diff

class LLM:
    def _init_(self,key=None):
        self.key = key or os.getenv("OPENAI_API_KEY")
        if self.key: openai.api_key = self.key
    def ask(self, prompt:str, model="gpt-3.5-turbo"):
        if not self.key:
            return "🔐 No API key set – showing local preview only."
        rsp = openai.ChatCompletion.create(model=model,
                messages=[{"role":"user","content":prompt}],max_tokens=800)
        return rsp.choices[0].message.content.strip()

# ---------- Flask -----------------------------------------------------------

app = Flask(__name__,template_folder="../frontend/templates",
                         static_folder="../frontend/static")
CORS(app)
masker, fixer, llm = PIIMasker(), Corrector(), LLM()

@app.route("/")
def home():      return render_template("index.html")

@app.route("/api/process_text", methods=["POST"])
def api():
    data = request.get_json();  raw = data.get("text","")
    if not raw: return jsonify(error="empty"), 400

    corrected, diffs = fixer.fix(raw)
    masked, mapping = masker.mask(corrected)
    coloured        = masker.colour(corrected)
    answer          = llm.ask(masked)

    return jsonify(
        corrected_text = corrected,
        masked_text    = masked,
        colored_text   = coloured,
        llm_response   = answer,
        corrections    = diffs,
        pii_analysis   = masker.detect(corrected),
    )

@app.route("/api/health")
def health():    return jsonify(status="ok", ts=datetime.utcnow().isoformat())

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)