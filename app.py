import gradio as gr
import re
import html
import csv
import io
import tempfile
from datetime import datetime
from difflib import SequenceMatcher
from langdetect import detect

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ── Optional dependencies (graceful fallback) ─────────────────────────────────
try:
    import pdfplumber
    PDF_READ = True
except ImportError:
    PDF_READ = False

try:
    from docx import Document as DocxDocument
    DOCX_SUPPORT = True
except ImportError:
    DOCX_SUPPORT = False


# ── Supported languages ───────────────────────────────────────────────────────
LANG_LABELS = {"auto": "🌐 Auto", "es": "🇪🇸 Español", "en": "🇬🇧 English",
               "fr": "🇫🇷 Français", "pt": "🇵🇹 Português"}

# ── Keywords per clause per language ─────────────────────────────────────────
KEYWORDS: dict[str, dict[str, list[str]]] = {
    "es": {
        "pagos":          ["pago","pagará","abonará","monto","importe","tarifa","honorario",
                           "remuneración","cuota","factura","transferencia","depósito","salario",
                           "bono","comisión","costo"],
        "penalizaciones": ["penalización","multa","interés moratorio","sanción","recargo",
                           "compensación","indemnización","daños","perjuicio"],
        "obligaciones":   ["deberá","se obliga","obligación","compromete","cumplir","garantizar",
                           "proveer","asegurar","entregar","informar"],
        "confidencialidad":["confidencialidad","no divulgación","NDA","información confidencial",
                            "datos sensibles","privada","secreto"],
        "terminación":    ["terminación","cancelación","rescisión","extinción","finalización",
                           "dar por terminado"],
    },
    "en": {
        "pagos":          ["payment","shall pay","fee","amount","rate","invoice","transfer",
                           "deposit","salary","bonus","remuneration"],
        "penalizaciones": ["penalty","fine","interest","surcharge","damages","indemnity"],
        "obligaciones":   ["shall","must","is obligated","required","comply","provide","deliver"],
        "confidencialidad":["confidentiality","non-disclosure","NDA","sensitive information",
                            "private","secret"],
        "terminación":    ["termination","cancellation","rescission","expiration","end of contract"],
    },
    "fr": {
        "pagos":          ["paiement","rémunération","montant","facture","honoraires","salaire"],
        "penalizaciones": ["pénalité","amende","sanction","dommages","indemnité"],
        "obligaciones":   ["devra","est tenu","obligation","s'engage","fournir","livrer"],
        "confidencialidad":["confidentialité","non-divulgation","information confidentielle","secret"],
        "terminación":    ["résiliation","annulation","expiration","fin du contrat"],
    },
    "pt": {
        "pagos":          ["pagamento","remuneração","valor","fatura","honorários","salário"],
        "penalizaciones": ["penalidade","multa","sanção","danos","indenização"],
        "obligaciones":   ["deverá","obriga-se","obrigação","comprometer","fornecer","entregar"],
        "confidencialidad":["confidencialidade","não divulgação","informação confidencial","segredo"],
        "terminación":    ["rescisão","cancelamento","extinção","término do contrato"],
    },
}

# ── Risk keywords per language ────────────────────────────────────────────────
RIESGOS: dict[str, dict[str, list[str]]] = {
    "es": {"Bajo":["recargo"], "Moderado":["penalización","sanción"],
           "Alto":["incumplimiento","daños"], "Crítico":["indemnización","perjuicio"]},
    "en": {"Bajo":["surcharge"], "Moderado":["penalty","fine"],
           "Alto":["breach","damages"], "Crítico":["indemnity","loss"]},
    "fr": {"Bajo":["supplément"], "Moderado":["pénalité","amende"],
           "Alto":["manquement","dommages"], "Crítico":["indemnité","préjudice"]},
    "pt": {"Bajo":["acréscimo"], "Moderado":["penalidade","multa"],
           "Alto":["inadimplemento","danos"], "Crítico":["indenização","prejuízo"]},
}

# ── Abusive clause patterns ───────────────────────────────────────────────────
ABUSIVAS: dict[str, list[str]] = {
    "es": ["a sola discreción","sin previo aviso","en cualquier momento y sin causa",
           "prórroga automática","renuncia irrevocable","sin responsabilidad alguna",
           "según estime conveniente","en tiempo razonable","a su entera discreción",
           "sin limitación alguna","sin necesidad de notificación","modificar en cualquier momento"],
    "en": ["at its sole discretion","without prior notice","at any time without cause",
           "automatic renewal","irrevocable waiver","without any liability",
           "as it deems appropriate","within reasonable time","without limitation",
           "without notice","modify at any time"],
    "fr": ["à sa seule discrétion","sans préavis","renouvellement automatique",
           "sans responsabilité","dans un délai raisonnable"],
    "pt": ["a seu exclusivo critério","sem aviso prévio","renovação automática",
           "sem qualquer responsabilidade","em prazo razoável"],
}

# ── Date / money regex ────────────────────────────────────────────────────────
DATE_PATTERNS = [
    r'\b\d{1,2}\s+de\s+\w+\s+de\s+\d{4}\b',
    r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
    r'\b\d{4}-\d{2}-\d{2}\b',
    r'\b\d{1,3}\s+días?\b',
    r'\b\d{1,2}\s+meses?\b',
    r'\b\d{1,2}\s+años?\b',
    r'\bwithin\s+\d+\s+(?:calendar\s+)?days?\b',
    r'\b\d+\s+business\s+days?\b',
    r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
]
MONEY_PATTERNS = [
    r'(?:USD|EUR|MXN|COP|ARS|GBP|BRL|€|\$|£)\s*[\d,\.]+',
    r'[\d,\.]+\s*(?:USD|EUR|MXN|COP|ARS|GBP|BRL|pesos?|euros?|dólares?|dollars?)',
]
PARTY_PATTERNS = [
    # denominado/referred to as → (company_name, alias)
    r'([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ\s\.]{3,55}?),?\s+(?:con\s+\w[\w\s\-]+?,\s+)?(?:en adelante|hereinafter)\s+(?:denominad[oa]|referred to as)\s+"?([^",\n]{3,35})"?',
    # entre X y Y → real company names
    r'(?:entre|between)\s+(?:la\s+empresa\s+|el\s+señor\s+|la\s+señora\s+)?([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s\.]{3,45}?)\s*,.*?(?:\sy\s|\sand\s)(?:la\s+empresa\s+|el\s+señor\s+|la\s+señora\s+)?([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s\.]{3,45}?)\s*(?:,|\.)',
]
_CLEAN_PREFIX = re.compile(
    r'^(?:entre\s+|between\s+|y\s+|and\s+|la\s+empresa\s+|el\s+señor\s+|la\s+señora\s+|the\s+company\s+)',
    re.IGNORECASE
)

CLAUSE_EMOJIS = {"pagos":"💰","penalizaciones":"⚠️","obligaciones":"📌","confidencialidad":"🔒","terminación":"❌"}
CLAUSE_COLORS = {"pagos":"#3b82f6","penalizaciones":"#f59e0b","obligaciones":"#8b5cf6","confidencialidad":"#10b981","terminación":"#ef4444"}
RISK_COLORS   = {"Bajo":"#22c55e","Moderado":"#f59e0b","Alto":"#ef4444","Crítico":"#7c3aed"}
RISK_ICONS    = {"Bajo":"🟢","Moderado":"🟡","Alto":"🔴","Crítico":"💀"}

# ═══════════════════════════════════════════════════════════════════════════════
# CORE ANALYSIS FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def generar_regex(palabras: list[str], ventana: int = 150) -> re.Pattern:
    escaped = [re.escape(w) for w in palabras]
    return re.compile(r".{0," + str(ventana) + r"}(" + "|".join(escaped) + r").{0," + str(ventana) + r"}", re.IGNORECASE | re.DOTALL)

def dividir_texto(texto: str, tamano: int = 2000) -> list[str]:
    return [texto[i:i+tamano] for i in range(0, len(texto), tamano)]

def detectar_idioma(texto: str, manual: str = "auto") -> str:
    if manual != "auto":
        return manual
    try:
        d = detect(texto)
        return d if d in KEYWORDS else "es"
    except:
        return "es"

def extraer_texto_archivo(archivo) -> str:
    if archivo is None:
        return ""
    nombre = archivo.name.lower()
    try:
        if nombre.endswith(".txt"):
            with open(archivo.name, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        elif nombre.endswith(".pdf"):
            if not PDF_READ:
                return "⚠️ pdfplumber no instalado. Instala con: pip install pdfplumber"
            texto = ""
            with pdfplumber.open(archivo.name) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        texto += t + "\n"
            return texto
        elif nombre.endswith(".docx"):
            if not DOCX_SUPPORT:
                return "⚠️ python-docx no instalado. Instala con: pip install python-docx"
            doc = DocxDocument(archivo.name)
            return "\n".join(p.text for p in doc.paragraphs)
    except Exception as e:
        return f"⚠️ Error al leer archivo: {e}"
    return ""

def extract_clauses(texto: str, lang: str, extra_kw: dict | None = None) -> tuple[dict, list]:
    kw = {k: list(v) for k, v in KEYWORDS.get(lang, KEYWORDS["es"]).items()}
    if extra_kw:
        for k, v in extra_kw.items():
            kw.setdefault(k, []).extend(v)
    patrones = {k: generar_regex(v) for k, v in kw.items()}
    frases = [f.strip() for f in re.split(r'\. |\.\n', texto) if f.strip()]
    clausulas = {k: [] for k in patrones}
    for i, f in enumerate(frases):
        for key, pat in patrones.items():
            if pat.search(f):
                clausulas[key].append({"ref": i + 1, "text": f})
    return clausulas, frases

def clasificar_riesgo(frase: str, lang: str) -> str:
    rmap = RIESGOS.get(lang, RIESGOS["es"])
    for nivel in ["Crítico", "Alto", "Moderado", "Bajo"]:
        for w in rmap[nivel]:
            if w.lower() in frase.lower():
                return nivel
    return ""

def detectar_riesgos(frases: list, lang: str) -> list:
    out = []
    for i, f in enumerate(frases):
        nivel = clasificar_riesgo(f, lang)
        if nivel:
            out.append({"ref": i + 1, "text": f, "nivel": f"{RISK_ICONS[nivel]} {nivel}", "nivel_raw": nivel})
    return out

def calcular_score(riesgos: list) -> int:
    pesos = {"Bajo": 1, "Moderado": 2, "Alto": 3, "Crítico": 4}
    return sum(pesos.get(r.get("nivel_raw", r["nivel"].split()[-1]), 0) for r in riesgos)

def label_score(score: int) -> str:
    if score <= 3:   return "🟢 Bajo"
    if score <= 6:   return "🟡 Moderado"
    if score <= 9:   return "🔴 Alto"
    return "💀 Crítico"

def extraer_fechas(texto: str) -> list[str]:
    out = []
    for p in DATE_PATTERNS:
        out += [m.group().strip() for m in re.finditer(p, texto, re.IGNORECASE)]
    return list(dict.fromkeys(out))

def extraer_montos(texto: str) -> list[str]:
    out = []
    for p in MONEY_PATTERNS:
        out += [m.group().strip() for m in re.finditer(p, texto, re.IGNORECASE)]
    return list(dict.fromkeys(out))

def extraer_partes(texto: str) -> list[str]:
    def _norm_key(s):
        s = _CLEAN_PREFIX.sub("", s).strip()
        return re.sub(r'[\s\.]+$', '', s).lower()

    found = []
    seen: set = set()
    for p in PARTY_PATTERNS:
        for m in re.findall(p, texto, re.IGNORECASE):
            parts = [m] if isinstance(m, str) else list(m)
            for raw in parts:
                raw = _CLEAN_PREFIX.sub("", raw).strip().strip('"').strip()
                raw = re.sub(r'[\s\.]+$', '', raw).strip()
                if len(raw) < 3:
                    continue
                key = _norm_key(raw)
                if any(key == s or key in s or s in key for s in seen):
                    continue
                seen.add(key)
                found.append(raw)
    return found[:8]

def detectar_abusivas(texto: str, lang: str) -> list:
    patrones = ABUSIVAS.get(lang, ABUSIVAS["es"])
    frases = [f.strip() for f in re.split(r'\. |\.\n', texto) if f.strip()]
    out = []
    for i, frase in enumerate(frases):
        for patron in patrones:
            if patron.lower() in frase.lower():
                out.append({"ref": i + 1, "text": frase, "patron": patron})
    return out

def estadisticas(texto: str) -> dict:
    palabras = len(texto.split())
    return {
        "Palabras": palabras,
        "Caracteres": len(texto),
        "Frases": len(re.split(r'\. |\.\n', texto)),
        "Páginas est.": max(1, round(palabras / 250)),
    }

def generar_checklist(clausulas: dict, plantilla: list | None = None) -> dict:
    plantilla = plantilla or list(KEYWORDS["es"].keys())
    return {c: "✅" if clausulas.get(c) else "✗" for c in plantilla}

# ═══════════════════════════════════════════════════════════════════════════════
# HTML DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

def _tag(items, color): return "".join(
    f"<span style='display:inline-block;margin:3px 2px;padding:3px 10px;border-radius:12px;background:{color};color:white;font-size:12px'>{html.escape(str(i))}</span>"
    for i in items) or "<span style='color:#9ca3af'>Ninguno detectado</span>"

def generar_dashboard(clausulas, riesgos, checklist, score, abusivas, fechas, montos, partes, stats, lang):
    score_label = label_score(score)
    score_color = RISK_COLORS.get(score_label.split()[-1], "#6b7280")
    score_pct   = min(100, score * 4)

    # Stats bar
    stats_html = "".join(
        f"<div style='flex:1;text-align:center;padding:12px;border-right:1px solid #f0f0f0'>"
        f"<div style='font-size:28px;font-weight:800;color:#1e293b'>{v}</div>"
        f"<div style='font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:.05em'>{k}</div></div>"
        for k, v in stats.items()
    )

    # Checklist
    checklist_html = "".join(
        f"<div style='display:inline-flex;align-items:center;gap:6px;margin:4px;padding:5px 14px;"
        f"border-radius:20px;background:{'#dcfce7' if v=='✅' else '#fee2e2'};"
        f"color:{'#166534' if v=='✅' else '#991b1b'};font-size:13px;font-weight:600'>"
        f"{v} {k}</div>"
        for k, v in checklist.items()
    )

    # Clause cards
    cards_html = ""
    for key, items in clausulas.items():
        c = CLAUSE_COLORS.get(key, "#6b7280")
        e = CLAUSE_EMOJIS.get(key, "📄")
        rows = "".join(
            f"<div style='padding:6px 0;border-bottom:1px solid #f1f5f9;font-size:12px;color:#475569'>"
            f"<span style='background:{c}22;color:{c};border-radius:4px;padding:1px 6px;font-size:10px;font-weight:700'>Ref {it['ref']}</span> "
            f"{html.escape(it['text'][:140])}{'…' if len(it['text'])>140 else ''}</div>"
            for it in items[:6]
        )
        extra = f"<div style='font-size:11px;color:#94a3b8;margin-top:4px'>+{len(items)-6} más…</div>" if len(items) > 6 else ""
        cards_html += (
            f"<div style='background:white;border-radius:12px;padding:16px;border-top:4px solid {c};"
            f"box-shadow:0 1px 4px rgba(0,0,0,.07);margin-bottom:12px'>"
            f"<div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:10px'>"
            f"<span style='font-size:15px;font-weight:700;color:#1e293b'>{e} {key.capitalize()}</span>"
            f"<span style='background:{c};color:white;border-radius:20px;padding:2px 12px;font-size:13px;font-weight:700'>{len(items)}</span></div>"
            f"{'<div style=\"color:#9ca3af;font-size:13px\">No encontrado</div>' if not items else rows + extra}</div>"
        )

    # Abusive clauses
    if abusivas:
        ab_html = "".join(
            f"<div style='background:#fff7ed;border-left:4px solid #f59e0b;padding:8px 12px;"
            f"margin:5px 0;border-radius:6px;font-size:12px;color:#78350f'>"
            f"⚠️ <b>«{html.escape(ab['patron'])}»</b> "
            f"<span style='color:#92400e'>[Ref {ab['ref']}]</span> — "
            f"{html.escape(ab['text'][:120])}…</div>"
            for ab in abusivas
        )
    else:
        ab_html = "<div style='color:#16a34a;font-size:13px'>✅ No se detectaron cláusulas potencialmente abusivas.</div>"

    # Risk list
    def _risk_row(r):
        nivel_key = r.get("nivel_raw", r["nivel"].split()[-1])
        color = RISK_COLORS.get(nivel_key, "#6b7280")
        return (
            f"<div style='background:white;border-left:4px solid {color};"
            f"padding:8px 12px;margin:5px 0;border-radius:6px;font-size:12px;"
            f"box-shadow:0 1px 3px rgba(0,0,0,.05)'>"
            f"<span style='font-weight:700'>[Ref {r['ref']}]</span> "
            f"{html.escape(r['text'][:160])} <b>→ {r['nivel']}</b></div>"
        )
    risk_html = "".join(_risk_row(r) for r in riesgos) or \
        "<div style='color:#16a34a;font-size:13px'>✅ Sin riesgos detectados.</div>"

    return f"""
<div style='font-family:"Segoe UI",system-ui,sans-serif;background:#f8fafc;padding:20px;border-radius:16px;max-width:960px;margin:0 auto'>

  <!-- Header -->
  <div style='background:linear-gradient(135deg,#0f172a 0%,#1e40af 100%);color:white;border-radius:14px;padding:24px 28px;margin-bottom:20px;display:flex;align-items:center;justify-content:space-between'>
    <div>
      <h2 style='margin:0;font-size:22px;font-weight:800;letter-spacing:-.03em'>📑 Contract Analyzer AI</h2>
      <p style='margin:4px 0 0;opacity:.65;font-size:13px'>Informe automático · {datetime.now().strftime("%d/%m/%Y %H:%M")} · Idioma: <b>{lang.upper()}</b></p>
    </div>
    <div style='background:rgba(255,255,255,.15);border-radius:10px;padding:10px 18px;text-align:center'>
      <div style='font-size:26px;font-weight:900'>{score}</div>
      <div style='font-size:11px;opacity:.8'>SCORE</div>
    </div>
  </div>

  <!-- Stats -->
  <div style='background:white;border-radius:12px;display:flex;margin-bottom:16px;box-shadow:0 1px 4px rgba(0,0,0,.06);overflow:hidden'>
    {stats_html}
  </div>

  <!-- Score bar -->
  <div style='background:white;border-radius:12px;padding:18px 22px;margin-bottom:16px;box-shadow:0 1px 4px rgba(0,0,0,.06)'>
    <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:10px'>
      <span style='font-weight:700;color:#1e293b'>📊 Score Global de Riesgo</span>
      <span style='font-size:18px;font-weight:800;color:{score_color}'>{score} → {score_label}</span>
    </div>
    <div style='background:#e2e8f0;border-radius:20px;height:10px'>
      <div style='background:{score_color};width:{score_pct}%;height:10px;border-radius:20px'></div>
    </div>
  </div>

  <!-- Checklist -->
  <div style='background:white;border-radius:12px;padding:18px 22px;margin-bottom:16px;box-shadow:0 1px 4px rgba(0,0,0,.06)'>
    <h3 style='margin:0 0 12px;font-size:15px;color:#1e293b'>📋 Checklist Legal</h3>
    {checklist_html}
  </div>

  <!-- Partes / Fechas / Montos -->
  <div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;margin-bottom:16px'>
    <div style='background:white;border-radius:12px;padding:16px;box-shadow:0 1px 4px rgba(0,0,0,.06)'>
      <h4 style='margin:0 0 10px;font-size:13px;color:#1e293b'>👥 Partes Identificadas</h4>
      {_tag(partes, "#8b5cf6")}
    </div>
    <div style='background:white;border-radius:12px;padding:16px;box-shadow:0 1px 4px rgba(0,0,0,.06)'>
      <h4 style='margin:0 0 10px;font-size:13px;color:#1e293b'>📅 Fechas y Plazos</h4>
      {_tag(fechas[:12], "#3b82f6")}
    </div>
    <div style='background:white;border-radius:12px;padding:16px;box-shadow:0 1px 4px rgba(0,0,0,.06)'>
      <h4 style='margin:0 0 10px;font-size:13px;color:#1e293b'>💰 Montos Detectados</h4>
      {_tag(montos[:12], "#10b981")}
    </div>
  </div>

  <!-- Abusivas -->
  <div style='background:white;border-radius:12px;padding:18px 22px;margin-bottom:16px;box-shadow:0 1px 4px rgba(0,0,0,.06)'>
    <h3 style='margin:0 0 12px;font-size:15px;color:#1e293b'>🚫 Cláusulas Potencialmente Abusivas</h3>
    {ab_html}
  </div>

  <!-- Clauses -->
  <div style='margin-bottom:16px'>
    <h3 style='font-size:15px;color:#1e293b;margin:0 0 12px'>📂 Cláusulas por Tipo</h3>
    {cards_html}
  </div>

  <!-- Risks -->
  <div style='background:white;border-radius:12px;padding:18px 22px;box-shadow:0 1px 4px rgba(0,0,0,.06)'>
    <h3 style='margin:0 0 12px;font-size:15px;color:#1e293b'>🚨 Riesgos Detectados</h3>
    {risk_html}
  </div>
</div>"""

# ═══════════════════════════════════════════════════════════════════════════════
# CHARTS
# ═══════════════════════════════════════════════════════════════════════════════

def generar_graficos(clausulas: dict, riesgos: list) -> str:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))
    fig.patch.set_facecolor("#f8fafc")

    # Bar – clauses per type
    names  = [k.capitalize() for k in clausulas]
    counts = [len(v) for v in clausulas.values()]
    colors = [CLAUSE_COLORS.get(k, "#6b7280") for k in clausulas]
    bars = ax1.bar(names, counts, color=colors, edgecolor="white", linewidth=1.5, width=0.6)
    ax1.set_facecolor("#f8fafc")
    ax1.set_title("Cláusulas por tipo", fontweight="bold", fontsize=13, pad=12)
    ax1.set_ylabel("Cantidad", fontsize=11)
    ax1.tick_params(axis="x", rotation=25, labelsize=10)
    ax1.spines[["top","right"]].set_visible(False)
    for bar, val in zip(bars, counts):
        ax1.text(bar.get_x() + bar.get_width()/2, val + .05, str(val),
                 ha="center", fontweight="bold", fontsize=11)

    # Pie – risk distribution
    niveles = {"Bajo": 0, "Moderado": 0, "Alto": 0, "Crítico": 0}
    for r in riesgos:
        k = r.get("nivel_raw", r["nivel"].split()[-1])
        niveles[k] = niveles.get(k, 0) + 1

    labels = [k for k, v in niveles.items() if v > 0]
    sizes  = [v for v in niveles.values() if v > 0]
    pie_colors = [RISK_COLORS[k] for k in labels]

    ax2.set_facecolor("#f8fafc")
    if sizes:
        wedges, texts, autotexts = ax2.pie(
            sizes, labels=labels, colors=pie_colors,
            autopct="%1.0f%%", startangle=140,
            wedgeprops={"edgecolor":"white","linewidth":2})
        for at in autotexts:
            at.set_fontweight("bold")
    else:
        ax2.text(0, 0, "Sin riesgos\ndetectados", ha="center", va="center",
                 fontsize=14, color="#16a34a", fontweight="bold")
        ax2.axis("off")
    ax2.set_title("Distribución de Riesgos", fontweight="bold", fontsize=13, pad=12)

    plt.tight_layout(pad=2)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(tmp.name, dpi=120, bbox_inches="tight", facecolor="#f8fafc")
    plt.close()
    return tmp.name

# ═══════════════════════════════════════════════════════════════════════════════
# COMPARATOR (side-by-side, stats, diff-only toggle)
# ═══════════════════════════════════════════════════════════════════════════════

def _word_diff(l1: str, l2: str) -> tuple[str, str]:
    m = SequenceMatcher(None, l1.split(), l2.split())
    left = right = ""
    for tag, i1, i2, j1, j2 in m.get_opcodes():
        w1 = " ".join(l1.split()[i1:i2])
        w2 = " ".join(l2.split()[j1:j2])
        if tag == "equal":
            left  += w1 + " "
            right += w2 + " "
        elif tag == "replace":
            left  += f"<mark style='background:#fca5a5;border-radius:3px'>{html.escape(w1)}</mark> "
            right += f"<mark style='background:#86efac;border-radius:3px'>{html.escape(w2)}</mark> "
        elif tag == "delete":
            left  += f"<mark style='background:#fca5a5;border-radius:3px;text-decoration:line-through'>{html.escape(w1)}</mark> "
        elif tag == "insert":
            right += f"<mark style='background:#86efac;border-radius:3px'>{html.escape(w2)}</mark> "
    return left.strip(), right.strip()

def comparar_contratos(a: str, b: str, solo_diffs: bool = False) -> str:
    if not a or not b:
        return "<p style='color:#ef4444;font-family:sans-serif'>⚠️ Introduce ambos contratos.</p>"

    lines1 = a.splitlines()
    lines2 = b.splitlines()
    s = SequenceMatcher(None, lines1, lines2)
    ratio   = round(s.ratio() * 100, 1)
    added = deleted = modified = 0

    col_a = col_b = ""
    ROW_BASE = "padding:3px 8px;font-size:12px;font-family:monospace;white-space:pre-wrap;word-break:break-word;"

    for tag, i1, i2, j1, j2 in s.get_opcodes():
        if tag == "equal":
            if not solo_diffs:
                for l in lines1[i1:i2]:
                    safe = html.escape(l) or "&nbsp;"
                    col_a += f"<div style='{ROW_BASE}'>{safe}</div>"
                    col_b += f"<div style='{ROW_BASE}'>{safe}</div>"
        elif tag == "delete":
            deleted += i2 - i1
            for l in lines1[i1:i2]:
                col_a += f"<div style='{ROW_BASE}background:#fee2e2'>{html.escape(l) or '&nbsp;'}</div>"
                col_b += f"<div style='{ROW_BASE}background:#f8fafc'>&nbsp;</div>"
        elif tag == "insert":
            added += j2 - j1
            for l in lines2[j1:j2]:
                col_a += f"<div style='{ROW_BASE}background:#f8fafc'>&nbsp;</div>"
                col_b += f"<div style='{ROW_BASE}background:#dcfce7'>{html.escape(l) or '&nbsp;'}</div>"
        elif tag == "replace":
            modified += max(i2-i1, j2-j1)
            for k in range(max(i2-i1, j2-j1)):
                l1 = lines1[i1+k] if i1+k < i2 else ""
                l2 = lines2[j1+k] if j1+k < j2 else ""
                dl, dr = _word_diff(l1, l2)
                col_a += f"<div style='{ROW_BASE}background:#fef3c7'>{dl or '&nbsp;'}</div>"
                col_b += f"<div style='{ROW_BASE}background:#ecfdf5'>{dr or '&nbsp;'}</div>"

    ratio_color = "#16a34a" if ratio > 80 else "#d97706" if ratio > 50 else "#dc2626"

    badge = lambda bg, text: (
        f"<span style='background:{bg};color:white;padding:5px 14px;border-radius:20px;"
        f"font-size:13px;font-weight:700'>{text}</span>"
    )

    return f"""
<div style='font-family:"Segoe UI",system-ui,sans-serif;padding:4px'>
  <div style='display:flex;gap:10px;margin-bottom:14px;flex-wrap:wrap'>
    {badge(ratio_color, f"📊 Similitud: {ratio}%")}
    {badge("#16a34a", f"➕ Añadidas: {added}")}
    {badge("#dc2626", f"➖ Eliminadas: {deleted}")}
    {badge("#d97706", f"✏️ Modificadas: {modified}")}
  </div>
  <div style='display:grid;grid-template-columns:1fr 1fr;border:1px solid #e2e8f0;border-radius:10px;overflow:hidden'>
    <div style='background:#fef2f2;padding:8px 14px;font-weight:700;font-size:13px;color:#991b1b;border-bottom:1px solid #e2e8f0'>📄 Contrato A</div>
    <div style='background:#f0fdf4;padding:8px 14px;font-weight:700;font-size:13px;color:#166534;border-bottom:1px solid #e2e8f0;border-left:1px solid #e2e8f0'>📄 Contrato B</div>
    <div style='padding:6px;max-height:520px;overflow-y:auto'>{col_a or "<div style='padding:8px;color:#9ca3af'>Sin diferencias</div>"}</div>
    <div style='padding:6px;max-height:520px;overflow-y:auto;border-left:1px solid #e2e8f0'>{col_b or "<div style='padding:8px;color:#9ca3af'>Sin diferencias</div>"}</div>
  </div>
</div>"""

# ═══════════════════════════════════════════════════════════════════════════════
# EXPORT FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def exportar_html(md: str) -> str | None:
    if not md:
        return None
    try:
        import markdown
        content = markdown.markdown(md)
    except ImportError:
        content = md.replace("\n", "<br>")
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8")
    tmp.write(f"<!DOCTYPE html><html><head><meta charset='utf-8'>"
              f"<style>body{{font-family:sans-serif;max-width:800px;margin:40px auto;padding:20px}}"
              f"h2{{color:#1e40af}}h3{{color:#1e293b}}</style></head><body>{content}</body></html>")
    tmp.close()
    return tmp.name


def exportar_csv(clausulas: dict, riesgos: list) -> str | None:
    if not clausulas:
        return None
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Tipo", "Ref", "Texto", "Nivel de Riesgo"])
    for tipo, items in clausulas.items():
        for it in items:
            w.writerow([tipo, it["ref"], it["text"], ""])
    for r in riesgos:
        w.writerow(["RIESGO", r["ref"], r["text"], r["nivel"]])
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode="w", encoding="utf-8", newline="")
    tmp.write(buf.getvalue()); tmp.close()
    return tmp.name

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ANALYSIS PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════

def analizar_contrato(texto, archivo, lang_manual, progress=gr.Progress()):
    # 1 – get text
    if archivo is not None:
        from_file = extraer_texto_archivo(archivo)
        if from_file and not from_file.startswith("⚠️"):
            texto = from_file
    if not texto or len(texto.strip()) < 40:
        return ("⚠️ El texto es demasiado corto o está vacío.", None, None, None, None)

    progress(0.10, desc="Detectando idioma…")
    lang = detectar_idioma(texto, lang_manual)

    progress(0.20, desc="Extrayendo cláusulas…")
    kw_keys = list(KEYWORDS.get(lang, KEYWORDS["es"]).keys())
    clausulas_totales: dict[str, list] = {k: [] for k in kw_keys}
    frases_totales: list[str] = []
    for bloque in dividir_texto(texto):
        cl, fr = extract_clauses(bloque, lang)
        for k in clausulas_totales:
            clausulas_totales[k].extend(cl.get(k, []))
        frases_totales.extend(fr)

    progress(0.45, desc="Analizando riesgos…")
    riesgos   = detectar_riesgos(frases_totales, lang)
    abusivas  = detectar_abusivas(texto, lang)
    fechas    = extraer_fechas(texto)
    montos    = extraer_montos(texto)
    partes    = extraer_partes(texto)
    stats     = estadisticas(texto)
    checklist = generar_checklist(clausulas_totales, kw_keys)
    score     = calcular_score(riesgos)

    progress(0.65, desc="Generando resumen…")
    clausulas_encontradas = [k for k, v in clausulas_totales.items() if v]
    partes_str = " · ".join(partes[:4]) if partes else "No identificadas"
    resumen_ai = (
        f"**Idioma:** {lang.upper()} · "
        f"**Palabras:** {stats['Palabras']} · "
        f"**Páginas est.:** {stats['Páginas est.']}\n\n"
        f"**Partes:** {partes_str}\n\n"
        f"**Cláusulas encontradas:** {', '.join(clausulas_encontradas) if clausulas_encontradas else 'Ninguna'}\n\n"
        f"**Riesgos detectados:** {len(riesgos)} "
        f"({'ninguno' if not riesgos else ', '.join(sorted(set(r['nivel'] for r in riesgos)))})\n\n"
        f"**Score global:** {score} → {label_score(score)}"
    )

    progress(0.82, desc="Generando visualizaciones…")
    dashboard = generar_dashboard(clausulas_totales, riesgos, checklist, score,
                                  abusivas, fechas, montos, partes, stats, lang)
    grafico   = generar_graficos(clausulas_totales, riesgos)

    # Markdown report
    md  = f"## 📑 Informe de Análisis · `{lang.upper()}`\n\n"
    md += f"### 📝 Resumen Ejecutivo\n{resumen_ai}\n\n"
    md += "### 📋 Checklist Legal\n" + "\n".join(f"- {k.capitalize()}: {v}" for k, v in checklist.items()) + "\n\n"
    if fechas:
        md += "### 📅 Fechas y Plazos\n" + "\n".join(f"- {f}" for f in fechas) + "\n\n"
    if montos:
        md += "### 💰 Montos\n" + "\n".join(f"- {m}" for m in montos) + "\n\n"
    if partes:
        md += "### 👥 Partes\n" + "\n".join(f"- {p}" for p in partes) + "\n\n"
    for key in kw_keys:
        e = CLAUSE_EMOJIS.get(key, "📄")
        items = clausulas_totales[key]
        md += f"### {e} {key.capitalize()}\n"
        md += "\n".join(f"- [Ref {it['ref']}] {it['text']}" for it in items) if items else "- No encontrado"
        md += "\n\n"
    if abusivas:
        md += f"### 🚫 Cláusulas Abusivas ({len(abusivas)})\n"
        md += "\n".join(f"- [Ref {ab['ref']}] «{ab['patron']}» → {ab['text'][:150]}" for ab in abusivas) + "\n\n"
    md += "### 🚨 Riesgos\n"
    md += "\n".join(f"- [Ref {r['ref']}] {r['text']} → {r['nivel']}" for r in riesgos) or "- Sin riesgos detectados"
    md += f"\n\n### 📊 Score Global: {score} → {label_score(score)}\n"

    progress(1.0, desc="¡Listo!")
    return md, dashboard, grafico, clausulas_totales, riesgos

# ═══════════════════════════════════════════════════════════════════════════════
# GRADIO UI
# ═══════════════════════════════════════════════════════════════════════════════

CSS = """
.gr-button-primary { background: #1e40af !important; }
footer { display: none !important; }
"""

with gr.Blocks(theme=gr.themes.Soft(primary_hue="blue"), css=CSS) as demo:
    gr.Markdown(
        "# 🤖 Contract Analyzer \n"
        "Análisis legal automatizado"
    )

    # Shared state
    state_clausulas = gr.State(value=None)
    state_riesgos   = gr.State(value=None)

    # ── Tab 1: Analyze ─────────────────────────────────────────────────────────
    with gr.Tab("📄 Analizar Contrato"):
        with gr.Row(equal_height=False):

            # Left panel – inputs
            with gr.Column(scale=1, min_width=300):
                archivo_input = gr.File(
                    label="📂 Subir contrato (.txt · .docx· .pdf)",
                    file_types=[".txt", ".pdf", ".docx"]
                )
                texto_input = gr.Textbox(
                    label="O pega el texto directamente",
                    lines=14,
                    placeholder="Pega aquí el texto del contrato…"
                )
                lang_input = gr.Dropdown(
                    choices=list(LANG_LABELS.keys()),
                    value="auto",
                    label="🌐 Idioma",
                    info="'auto' detecta automáticamente"
                )
                boton_analizar = gr.Button("🔍 Analizar", variant="primary", size="lg")
                gr.Markdown("---")
                with gr.Row():
                    boton_html = gr.Button("📄 HTML")
                    boton_csv  = gr.Button("📊 CSV")
                file_html = gr.File(label="Descarga HTML", visible=True)
                file_csv  = gr.File(label="Descarga CSV",  visible=True)

            # Right panel – outputs
            with gr.Column(scale=2):
                with gr.Tabs():
                    with gr.Tab("📊 Dashboard"):
                        out_dashboard = gr.HTML()
                    with gr.Tab("📝 Informe"):
                        out_markdown  = gr.Markdown()
                    with gr.Tab("📈 Gráficos"):
                        out_grafico   = gr.Image(label="Distribución")

        # Events
        boton_analizar.click(
            fn=analizar_contrato,
            inputs=[texto_input, archivo_input, lang_input],
            outputs=[out_markdown, out_dashboard, out_grafico, state_clausulas, state_riesgos],
        )
        boton_html.click(fn=exportar_html, inputs=out_markdown,  outputs=file_html)
        boton_csv.click(
            fn=lambda cl, ri: exportar_csv(cl, ri) if cl else None,
            inputs=[state_clausulas, state_riesgos],
            outputs=file_csv
        )

    # ── Tab 2: Compare ─────────────────────────────────────────────────────────
    with gr.Tab("🔍 Comparar Contratos"):
        with gr.Row():
            cont_a = gr.Textbox(label="📄 Contrato A", lines=18, placeholder="Pega el contrato A…")
            cont_b = gr.Textbox(label="📄 Contrato B", lines=18, placeholder="Pega el contrato B…")
        with gr.Row():
            solo_diffs   = gr.Checkbox(label="Mostrar solo diferencias", value=False)
            boton_comparar = gr.Button("▶ Comparar", variant="primary")
        out_diff = gr.HTML()
        boton_comparar.click(
            fn=comparar_contratos,
            inputs=[cont_a, cont_b, solo_diffs],
            outputs=out_diff
        )

demo.launch()
