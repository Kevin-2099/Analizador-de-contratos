import gradio as gr
import re
from difflib import SequenceMatcher
from transformers import pipeline
from langdetect import detect
import html

# -----------------------------
# Modelo de resumen
# -----------------------------
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

# -----------------------------
# Plantilla legal estándar
# -----------------------------
plantilla_clausulas = ["pagos","penalizaciones","obligaciones","confidencialidad","terminación"]

# -----------------------------
# Palabras clave por cláusula
# -----------------------------
pagos_kw_es = ["pago","pagará","abonará","monto","importe","tarifa","honorario","remuneración","cuota","factura","transferencia","depósito","salario","bono","comisión","costo"]
penalizaciones_kw_es = ["penalización","multa","interés moratorio","sanción","recargo","compensación","indemnización","daños","perjuicio"]
obligaciones_kw_es = ["deberá","se obliga","obligación","compromete","cumplir","garantizar","proveer","asegurar","entregar","informar"]
confidencialidad_kw_es = ["confidencialidad","no divulgación","NDA","información confidencial","datos sensibles","privada","secreto"]
terminacion_kw_es = ["terminación","cancelación","rescisión","extinción","finalización","dar por terminado"]

pagos_kw_en = ["payment","shall pay","fee","amount","rate","invoice","transfer","deposit","salary","bonus"]
penalizaciones_kw_en = ["penalty","fine","interest","surcharge","damages","indemnity"]
obligaciones_kw_en = ["shall","must","is obligated","required","comply","provide","deliver"]
confidencialidad_kw_en = ["confidentiality","non-disclosure","NDA","sensitive information","private","secret"]
terminacion_kw_en = ["termination","cancellation","rescission","expiration","end of contract"]

# -----------------------------
# Riesgos
# -----------------------------
riesgos_es = {
    "Bajo":["recargo"],
    "Moderado":["penalización","sanción"],
    "Alto":["incumplimiento","daños"],
    "Crítico":["indemnización","perjuicio"]
}

riesgos_en = {
    "Bajo":["surcharge"],
    "Moderado":["penalty","fine"],
    "Alto":["breach","damages"],
    "Crítico":["indemnity","loss"]
}

# -----------------------------
# Regex generator
# -----------------------------
def generar_regex_clausula(palabras, ventana=150):
    escaped=[re.escape(w) for w in palabras]
    pattern=r".{0,"+str(ventana)+r"}("+ "|".join(escaped)+ r").{0,"+str(ventana)+r"}"
    return re.compile(pattern,re.IGNORECASE|re.DOTALL)

# -----------------------------
# División texto grande
# -----------------------------
def dividir_texto(texto,tamano=2000):
    return [texto[i:i+tamano] for i in range(0,len(texto),tamano)]

# -----------------------------
# Extracción cláusulas
# -----------------------------
def extract_clauses(texto,lang):

    if lang=="en":
        patrones={
            "pagos":generar_regex_clausula(pagos_kw_en),
            "penalizaciones":generar_regex_clausula(penalizaciones_kw_en),
            "obligaciones":generar_regex_clausula(obligaciones_kw_en),
            "confidencialidad":generar_regex_clausula(confidencialidad_kw_en),
            "terminación":generar_regex_clausula(terminacion_kw_en)
        }
    else:
        patrones={
            "pagos":generar_regex_clausula(pagos_kw_es),
            "penalizaciones":generar_regex_clausula(penalizaciones_kw_es),
            "obligaciones":generar_regex_clausula(obligaciones_kw_es),
            "confidencialidad":generar_regex_clausula(confidencialidad_kw_es),
            "terminación":generar_regex_clausula(terminacion_kw_es)
        }

    frases=re.split(r'\. |\.\n',texto)
    frases=[f.strip() for f in frases if f.strip()]

    clausulas={k:[] for k in patrones}

    for i,f in enumerate(frases):
        for key,pattern in patrones.items():
            if pattern.search(f):
                clausulas[key].append({"ref":i+1,"text":f})

    return clausulas,frases

# -----------------------------
# Clasificación riesgo
# -----------------------------
def clasificar_riesgo(frase,lang):

    riesgos=riesgos_en if lang=="en" else riesgos_es

    for nivel in ["Crítico","Alto","Moderado","Bajo"]:
        for palabra in riesgos[nivel]:
            if palabra.lower() in frase.lower():
                return nivel

    return ""

# -----------------------------
# Detectar riesgos
# -----------------------------
def detectar_riesgos(frases,lang):

    riesgos=[]

    for i,f in enumerate(frases):

        nivel=clasificar_riesgo(f,lang)

        if nivel:
            icono={
                "Bajo":"🟢 Bajo",
                "Moderado":"🟡 Moderado",
                "Alto":"🔴 Alto",
                "Crítico":"💀 Crítico"
            }[nivel]

            riesgos.append({"ref":i+1,"text":f,"nivel":icono})

    return riesgos

# -----------------------------
# Score riesgos
# -----------------------------
def calcular_score_riesgo(riesgos):

    pesos={"Bajo":1,"Moderado":2,"Alto":3,"Crítico":4}
    score=0

    for r in riesgos:
        nivel=r["nivel"].split()[-1]
        score+=pesos.get(nivel,0)

    return score

def icono_score(score):

    if score<=3:
        return "🟢 Bajo"
    elif score<=6:
        return "🟡 Moderado"
    elif score<=9:
        return "🔴 Alto"
    else:
        return "💀 Crítico"

# -----------------------------
# Checklist legal
# -----------------------------
def generar_checklist(clausulas):

    checklist={}

    for c in plantilla_clausulas:
        checklist[c]="✅" if clausulas.get(c) else "✗"

    return checklist

# =============================
# COMPARADOR VISUAL
# =============================

def highlight_word_diff(line1,line2):

    matcher=SequenceMatcher(None,line1.split(),line2.split())
    result=""

    for tag,i1,i2,j1,j2 in matcher.get_opcodes():

        if tag=="equal":
            result+=" ".join(line1.split()[i1:i2])+" "

        elif tag=="replace":
            result+=f"<span style='background-color:#ffcccc'>{' '.join(line1.split()[i1:i2])}</span> "
            result+=f"<span style='background-color:#ccffcc'>{' '.join(line2.split()[j1:j2])}</span> "

        elif tag=="delete":
            result+=f"<span style='background-color:#ffcccc'>{' '.join(line1.split()[i1:i2])}</span> "

        elif tag=="insert":
            result+=f"<span style='background-color:#ccffcc'>{' '.join(line2.split()[j1:j2])}</span> "

    return result.strip()

def highlight_changes_colors(text1,text2):

    html_diff=""

    lines1=text1.splitlines()
    lines2=text2.splitlines()

    s=SequenceMatcher(None,lines1,lines2)

    for tag,i1,i2,j1,j2 in s.get_opcodes():

        if tag=="equal":
            for l1 in lines1[i1:i2]:
                html_diff+=html.escape(l1)+"<br>"

        else:

            max_lines=max(i2-i1,j2-j1)

            for k in range(max_lines):

                l1=lines1[i1+k] if i1+k<i2 else ""
                l2=lines2[j1+k] if j1+k<j2 else ""

                html_diff+=highlight_word_diff(l1,l2)+"<br>"

    return html_diff

def comparar_contratos(a,b):

    if not a or not b:
        return "<p style='color:red'>Introduce ambos contratos.</p>"

    diff=highlight_changes_colors(a,b)

    return f"""
    <h3>Comparación de Contratos</h3>

    <p>
    <span style='background-color:#ffcccc'>Texto eliminado</span> |
    <span style='background-color:#ccffcc'>Texto añadido</span>
    </p>

    {diff}
    """

# -----------------------------
# Exportar HTML
# -----------------------------
def exportar_html(md):

    import markdown
    import tempfile

    html_content=markdown.markdown(md)

    tmp=tempfile.NamedTemporaryFile(delete=False,suffix=".html",mode="w",encoding="utf-8")

    tmp.write(html_content)
    tmp.close()

    return tmp.name

# -----------------------------
# Analizar contrato
# -----------------------------
def analizar_contrato(texto):

    try:

        lang="es" if detect(texto)=="es" else "en"

        bloques=dividir_texto(texto)

        clausulas_totales={
            "pagos":[],
            "penalizaciones":[],
            "obligaciones":[],
            "confidencialidad":[],
            "terminación":[]
        }

        frases_totales=[]

        for b in bloques:

            clausulas,frases=extract_clauses(b,lang)

            for k in clausulas_totales:
                clausulas_totales[k].extend(clausulas[k])

            frases_totales.extend(frases)

        riesgos=detectar_riesgos(frases_totales,lang)

        resumen_ai=summarizer(texto,max_length=200,min_length=60,do_sample=False)[0]["summary_text"]

        salida="## 📑 Informe de Análisis de Contrato\n\n"

        salida+="### 📝 Resumen Ejecutivo\n"+resumen_ai+"\n\n"

        checklist=generar_checklist(clausulas_totales)

        salida+="### 📋 Checklist Legal\n"

        for k,v in checklist.items():
            salida+=f"- {k.capitalize()}: {v}\n"

        salida+="\n"

        for key,emoji in [
            ("pagos","💰"),
            ("penalizaciones","⚠️"),
            ("obligaciones","📌"),
            ("confidencialidad","🔒"),
            ("terminación","❌")
        ]:

            salida+=f"### {emoji} {key.capitalize()}\n"

            items=clausulas_totales[key]

            if not items:
                salida+="- No encontrado\n\n"

            else:
                for it in items:
                    salida+=f"- [Ref {it['ref']}] {it['text']}\n"
                salida+="\n"

        salida+="### 🚨 Riesgos Potenciales\n"

        for r in riesgos:
            salida+=f"- [Ref {r['ref']}] {r['text']} → {r['nivel']}\n"

        score=calcular_score_riesgo(riesgos)

        salida+=f"\n### 📊 Score Global de Riesgo: {score} → {icono_score(score)}\n"

        return salida

    except Exception as e:

        return f"Error: {str(e)}"

# -----------------------------
# Interfaz Gradio
# -----------------------------
with gr.Blocks() as demo:

    gr.Markdown("## 🤖 Contract Analyzer AI")

    with gr.Tab("Analizar contrato"):

        with gr.Row():

            with gr.Column():

                input_text=gr.Textbox(label="Texto del contrato",lines=25)

                boton=gr.Button("Analizar")

                output_file=gr.File(label="Descargar HTML")

                boton_exportar=gr.Button("Exportar HTML")

            with gr.Column():

                output_text=gr.Markdown()

        boton.click(fn=analizar_contrato,inputs=input_text,outputs=output_text)

        boton_exportar.click(fn=exportar_html,inputs=output_text,outputs=output_file)

    with gr.Tab("Comparar contratos"):

        with gr.Row():

            contrato_a=gr.Textbox(label="Contrato A",lines=20)
            contrato_b=gr.Textbox(label="Contrato B",lines=20)

        boton_comparar=gr.Button("Comparar")

        salida_diff=gr.HTML()

        boton_comparar.click(fn=comparar_contratos,inputs=[contrato_a,contrato_b],outputs=salida_diff)

demo.launch()
