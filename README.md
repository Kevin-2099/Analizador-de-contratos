# 📑 Contract Analyzer / Analizador de Contratos

Este proyecto es una aplicación interactiva construida con Gradio, diseñada para analizar textos contractuales en español e inglés, generar un resumen ejecutivo, identificar cláusulas clave, calcular un score global de riesgo y comparar versiones de contratos.

## 🚀 Funcionalidades
- 🔍 Detección automática de idioma

  - El sistema utiliza langdetect para determinar si el contrato está en español o inglés, y aplica listas de palabras clave específicas por idioma.

- 🧠 Resumen automático

  - Genera un resumen ejecutivo claro y conciso utilizando el modelo sshleifer/distilbart-cnn-12-6 de Transformers.

- 🧩 Extracción de cláusulas

  - Identifica y organiza información relevante en categorías estándar:

    - 📆 Fechas
    
    - 💰 Pagos
    
    - ⚠️ Penalizaciones
    
    - 📌 Obligaciones
    
    - 🔒 Confidencialidad
    
    - ❌ Términos de terminación

  - Cada cláusula incluye una referencia de frase [Ref X] para localizarla fácilmente en el texto original.

- 🚨 Detección de riesgos

  - Detecta frases relacionadas con riesgos contractuales y las clasifica según su severidad:

    - 🟢 Bajo
    
    - 🟡 Moderado
    
    - 🔴 Alto
    
    - 💀 Crítico

  - El sistema ignora riesgos en contextos seguros, como acuerdos mutuos o cláusulas opcionales. Además, calcula un score global de riesgo que resume el nivel general del contrato.

- 📋 Checklist legal

  - Genera un checklist rápido de las cláusulas presentes o ausentes en el contrato con ✅ o ✗.

- 🔍 Comparación de contratos

  - Permite comparar dos versiones de un contrato resaltando visualmente:

    - Texto eliminado (rojo)
    
    - Texto añadido (verde)

  - Esto facilita la revisión de cambios entre versiones.

- 🧾 Reporte estructurado

  - El informe final incluye:

    - Resumen ejecutivo
    
    - Fechas detectadas
    
    - Cláusulas clasificadas con referencias
    
    - Riesgos potenciales con nivel y referencia
    
    - Checklist legal
    
    - Score global de riesgo

  - Además, se puede exportar el informe a HTML para compartir o guardar.

## 🛠️ Tecnologías utilizadas

- Python 3.10+

- Gradio

- Transformers (Hugging Face)

- langdetect

- Regex

- Difflib (SequenceMatcher)

- Pipeline de summarization

## ⚡ Uso

- Copia y pega un texto de contrato en el cuadro izquierdo.

- Haz clic en “Analizar”.

- En el lado derecho aparecerá:

  - Resumen ejecutivo
  
  - Fechas detectadas
  
  - Cláusulas con referencias
  
  - Riesgos potenciales con nivel
  
  - Checklist legal
  
  - Score global de riesgo

- Opcional: exporta el informe a HTML.

- Para comparar contratos, pega dos versiones y haz clic en “Comparar” para ver las diferencias resaltadas.

## 💡 Notas

Este Space no reemplaza a un abogado.

Es una herramienta de apoyo para extracción rápida de información.

El análisis se basa en coincidencias por palabras clave y modelos estadísticos.

## 📄 Licencia

Este proyecto se distribuye bajo una **licencia propietaria con acceso al código (source-available)**.

El código fuente se pone a disposición únicamente para fines de **visualización, evaluación y aprendizaje**.

❌ No está permitido copiar, modificar, redistribuir, sublicenciar, ni crear obras derivadas del software o de su código fuente sin autorización escrita expresa del titular de los derechos.

❌ El uso comercial del software, incluyendo su oferta como servicio (SaaS), su integración en productos comerciales o su uso en entornos de producción, requiere un **acuerdo de licencia comercial independiente**.

📌 El texto **legalmente vinculante** de la licencia es la versión en inglés incluida en el archivo `LICENSE`. 

Se proporciona una traducción al español en `LICENSE_ES.md` únicamente con fines informativos. En caso de discrepancia, prevalece la versión en inglés.

## Autor
Kevin-2099
