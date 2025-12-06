import gradio as gr
import re
from transformers import pipeline
from langdetect import detect

# -----------------------------
# Modelo de resumen
# -----------------------------
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

# -----------------------------
# Palabras clave por cláusula
# -----------------------------
pagos_kw_es = ["pago","pagará","abonará","fee","monto","importe","tarifa","honorario","remuneración","cuota","valor","factura","transferencia","abono","depósito","salario","bono","comisión","costo","transferirá","enviará"]
penalizaciones_kw_es = ["penalización","multa","interés moratorio","sanción","recargo","compensación","indemnización","daños","costas","perjuicio","se añadirá","cargo adicional"]
obligaciones_kw_es = ["deberá","se obliga","tiene la obligación","compromete","cumplir","garantizar","proveer","asegurar","entregar","informar"]
confidencialidad_kw_es = [
    "confidencialidad","no divulgación","NDA","información sensible","protegida","privada","secreto","restricción","reservada","privilegios",
    "mantener en reserva","no divulgar","divulgar","protegidos","documentos privados","información confidencial","material compartido","datos sensibles"
]
terminacion_kw_es = ["terminación","resolución","finalización del contrato","cancelación","vencimiento","rescisión","extinción","conclusión","fin","anulación","cancelarse","finalizar","dar por terminado","terminar contrato","concluir"]

pagos_kw_en = ["payment","shall pay","will pay","fee","amount","charge","rate","compensation","remuneration","installment","value","invoice","transfer","deposit","salary","bonus","commission","cost","transfer","send"]
penalizaciones_kw_en = ["penalty","fine","late fee","interest","surcharge","compensation","damages","indemnity","liability","loss","add","extra charge"]
obligaciones_kw_en = ["shall","must","is obligated","is required","commits to","comply","ensure","provide","deliver","inform","guarantee"]
confidencialidad_kw_en = [
    "confidentiality","non-disclosure","NDA","sensitive information","protected","private","secret","restriction","confidential","privileged",
    "keep confidential","not disclose","disclose","protected files","private information","shared materials","sensitive data"
]
terminacion_kw_en = ["termination","resolution","end of contract","cancellation","expiration","rescission","extinction","conclusion","end","annulment","cancel","terminate","end the contract","rescind","conclude"]

# -----------------------------
# Palabras de riesgo por nivel
# -----------------------------
riesgos_es = {
    "Bajo": ["recargo","interés menor","extra menor"],
    "Moderado": ["penalización","multa leve","sanción","compensación"],
    "Alto": ["incumplimiento","daños","coste adicional","responsabilidad"],
    "Crítico": ["indemnización","perjuicio","daños graves","pérdida significativa"]
}

riesgos_en = {
    "Bajo": ["surcharge","minor fee","small extra"],
    "Moderado": ["penalty","fine","interest","compensation"],
    "Alto": ["breach","damages","extra cost","liability","responsibility"],
    "Crítico": ["indemnity","loss","major damages","significant loss"]
}

# -----------------------------
# Contexto seguro (anula riesgo)
# -----------------------------
contexto_seguro_es = ["según acuerdo mutuo","ejemplo","opcional","no se aplicará realmente"]
contexto_seguro_en = ["mutual agreement","example","optional","will not apply"]

# -----------------------------
# Generar regex
# -----------------------------
def generar_regex_clausula(palabras, ventana=150):
    escaped = [re.escape(w) for w in palabras]
    pattern = r".{0," + str(ventana) + r"}(" + "|".join(escaped) + r").{0," + str(ventana) + r"}"
    return re.compile(pattern, re.IGNORECASE | re.DOTALL)

# -----------------------------
# Extracción de cláusulas con referencias
# -----------------------------
def extract_clauses(texto, lang):
    if lang=="en":
        patrones = {
            "pagos": generar_regex_clausula(pagos_kw_en),
            "penalizaciones": generar_regex_clausula(penalizaciones_kw_en),
            "obligaciones": generar_regex_clausula(obligaciones_kw_en),
            "confidencialidad": generar_regex_clausula(confidencialidad_kw_en),
            "terminación": generar_regex_clausula(terminacion_kw_en)
        }
    else:
        patrones = {
            "pagos": generar_regex_clausula(pagos_kw_es),
            "penalizaciones": generar_regex_clausula(penalizaciones_kw_es),
            "obligaciones": generar_regex_clausula(obligaciones_kw_es),
            "confidencialidad": generar_regex_clausula(confidencialidad_kw_es),
            "terminación": generar_regex_clausula(terminacion_kw_es)
        }

    patron_fecha = re.compile(r"\b(?:\d{1,2}[\/\.-]\d{1,2}[\/\.-]\d{2,4}|\d{4}-\d{2}-\d{2})\b")
    frases = re.split(r'\. |\.\n', texto)
    frases = [f.strip() for f in frases if f.strip()]

    clausulas = {k: [] for k in patrones}
    clausulas["fechas"] = [{"ref": None, "text": f} for f in patron_fecha.findall(texto)]

    for i, f in enumerate(frases):
        for key, pattern in patrones.items():
            if pattern.search(f):
                clausulas[key].append({"ref": i+1, "text": f})

    return clausulas, frases

# -----------------------------
# Clasificación de riesgo con contexto seguro
# -----------------------------
def clasificar_riesgo(frase, lang):
    if lang=="en":
        riesgos = riesgos_en
        contexto_seguro = contexto_seguro_en
    else:
        riesgos = riesgos_es
        contexto_seguro = contexto_seguro_es

    if any(cs.lower() in frase.lower() for cs in contexto_seguro):
        return ""

    for nivel in ["Crítico","Alto","Moderado","Bajo"]:
        for palabra in riesgos[nivel]:
            if re.search(rf"(.{{0,50}}{re.escape(palabra)}.{{0,50}}(\$\d+|\d+%|valor total)?)", frase, re.IGNORECASE):
                return nivel
    return ""

# -----------------------------
# Detección de riesgos
# -----------------------------
def detectar_riesgos(clausulas, frases, lang):
    riesgos = []
    for i, f in enumerate(frases):
        nivel = clasificar_riesgo(f, lang)
        if nivel:
            icono = {"Bajo":"⚠️ Bajo","Moderado":"⚠️ Moderado","Alto":"🔥 Alto","Crítico":"💀 Crítico"}[nivel]
            riesgos.append({"ref": i+1, "text": f, "nivel": icono})

    if not riesgos:
        riesgos.append({"ref": None, "text": "No se detectaron riesgos significativos." if lang=="es" else "No significant risks detected.", "nivel": ""})
    return riesgos

# -----------------------------
# Normalizar lista
# -----------------------------
def normalizar_lista(lst):
    if lst and isinstance(lst[0], dict):
        return lst
    return list(dict.fromkeys(lst))

# -----------------------------
# Análisis principal
# -----------------------------
def analizar_contrato(texto):
    try:
        lang = "es" if detect(texto)=="es" else "en"
        clausulas, frases = extract_clauses(texto, lang)
        riesgos = detectar_riesgos(clausulas, frases, lang)
        resumen_ai = summarizer(texto, max_length=250, min_length=80, do_sample=False)[0]["summary_text"]

        salida = f"## 📑 {'Informe de Análisis de Contrato' if lang=='es' else 'Contract Analysis Report'}\n\n"
        salida += f"### 📝 {'Resumen Ejecutivo' if lang=='es' else 'Executive Summary'}\n{resumen_ai}\n\n"

        for key, emoji in [("fechas","📆"),("pagos","💰"),("penalizaciones","⚠️"),("obligaciones","📌"),("confidencialidad","🔒"),("terminación","❌")]:
            salida += f"### {emoji} {key.capitalize()}\n"
            items = clausulas[key]
            if not items:
                salida += "- " + ("No se encontró información." if lang=="es" else "Not found.") + "\n\n"
            else:
                for it in items:
                    salida += f"- [Ref {it['ref']}] {it['text']}\n" if it['ref'] else f"- {it['text']}\n"
                salida += "\n"

        salida += f"### 🚨 {'Riesgos Potenciales' if lang=='es' else 'Potential Risks'}\n"
        for r in riesgos:
            ref_text = f"[Ref {r['ref']}] " if r['ref'] else ""
            salida += f"- {ref_text}{r['text']} {r['nivel']}\n"

        return salida

    except Exception as e:
        return f"Error: {str(e)}"

# -----------------------------
# Interfaz Gradio
# -----------------------------
with gr.Blocks() as demo:
    gr.Markdown("## 🤖 Contract Analyzer / Analizador de Contratos")
    gr.Markdown("Paste a contract text on the left to extract clauses, detect risks, and generate an executive summary.")

    with gr.Row():
        with gr.Column(scale=1):
            input_text = gr.Textbox(label="Contract Text / Texto del Contrato", placeholder="Paste the contract here...", lines=25)
            boton = gr.Button("Analyze / Analizar")
        with gr.Column(scale=1):
            output_text = gr.Markdown()

    boton.click(fn=analizar_contrato, inputs=input_text, outputs=output_text)

demo.launch()
