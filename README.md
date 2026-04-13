# 📑 Contract Analyzer AI / Analizador de Contratos

Aplicación avanzada de análisis contractual construida con Gradio. Permite analizar contratos de forma automática, detectar riesgos, identificar cláusulas clave, extraer información relevante y comparar versiones con visualización profesional tipo dashboard.

## 🚀 Funcionalidades
- 🌍 Multi-idioma inteligente
  - Detección automática o manual del idioma
  - Soporte para:
    - 🇪🇸 Español
    - 🇬🇧 Inglés
    - 🇫🇷 Francés
    - 🇵🇹 Portugués
- 📂 Soporte de archivos
  - Analiza contratos desde:
    - .txt
    - .pdf
    - .docx
  - También puedes pegar el texto manualmente
- 📊 Dashboard visual profesional
  - Interfaz moderna con:
    - Score de riesgo con barra visual
    - Tarjetas por tipo de cláusula
    - Estadísticas del documento
    - Visualización clara de resultados
- 🧩 Extracción de cláusulas
  - Identifica automáticamente:
    - 💰 Pagos
    - ⚠️ Penalizaciones
    - 📌 Obligaciones
    - 🔒 Confidencialidad
    - ❌ Terminación
  - Cada cláusula incluye referencia:
    - [Ref X]
- 🚨 Detección de riesgos
  - Clasificación automática por severidad:
    - 🟢 Bajo
    - 🟡 Moderado
    - 🔴 Alto
    - 💀 Crítico
  - ✔️ Incluye:
    - Lista de riesgos detectados
    - Distribución visual
    - Score global de riesgo
- 🚫 Detección de cláusulas abusivas
  - Identifica patrones problemáticos como:
    - “a sola discreción”
    - “sin previo aviso”
    - “renovación automática”
    - “sin responsabilidad”
- 📅 Extracción de información clave
  - Detecta automáticamente:
    - 📅 Fechas y plazos
    - 💰 Montos económicos
    - 👥 Partes del contrato
- 📈 Visualización de datos
  - Gráfico de barras → cláusulas por tipo
  - Gráfico circular → distribución de riesgos
- 📋 Checklist legal automático
  - Verifica presencia de cláusulas clave
  - Resultado visual:
    - ✅ Presente
    - ✗ Ausente
- 🔍 Comparador de contratos avanzado
  - Comparación lado a lado
  - Resalta:
    - ➕ Añadidos
    - ➖ Eliminados
    - ✏️ Modificados
  - Incluye:
    - % de similitud
    - Métricas de cambios
    - Opción: mostrar solo diferencias
- 📤 Exportación de resultados
    - 📄 HTML (informe completo)
    - 📊 CSV (datos estructurados)
    - 🧾 Informe estructurado

  Incluye:
    - Resumen ejecutivo
    - Estadísticas del documento
    - Partes identificadas
    - Fechas y montos
    - Cláusulas clasificadas
    - Riesgos detectados
    - Cláusulas abusivas
    - Checklist legal
    - Score global de riesgo
## 🛠️ Tecnologías utilizadas
  - Python 3.10+
  - Gradio
  - langdetect
  - Regex
  - Difflib (SequenceMatcher)
  - Matplotlib
  - pdfplumber (opcional)
  - python-docx (opcional)
## ⚡ Uso
- 🔍 Análisis
  - Sube un archivo o pega el contrato
  - Selecciona idioma (o auto)
  - Haz clic en Analizar
  - Visualiza:
    - Dashboard
    - Informe
    - Gráficos
- 🔍 Comparación
  - Pega dos contratos
  - (Opcional) activa “solo diferencias”
  - Haz clic en Comparar
- 📤 Exportación
  - Exporta el análisis en:
    - HTML
    - CSV
## 💡 Notas
  - Esta herramienta no sustituye asesoramiento legal profesional
  - Diseñada para:
    - Análisis rápido
    - Revisión preliminar
    - Apoyo en lectura de contratos
  - El sistema se basa en:
    - Reglas heurísticas (keywords + regex)
    - Procesamiento automático de texto
## 📄 Licencia

Este proyecto se distribuye bajo una **licencia propietaria con acceso al código (source-available)**.

El código fuente se pone a disposición únicamente para fines de **visualización, evaluación y aprendizaje**.

❌ No está permitido copiar, modificar, redistribuir, sublicenciar, ni crear obras derivadas del software o de su código fuente sin autorización escrita expresa del titular de los derechos.

❌ El uso comercial del software, incluyendo su oferta como servicio (SaaS), su integración en productos comerciales o su uso en entornos de producción, requiere un **acuerdo de licencia comercial independiente**.

📌 El texto **legalmente vinculante** de la licencia es la versión en inglés incluida en el archivo `LICENSE`. 

Se proporciona una traducción al español en `LICENSE_ES.md` únicamente con fines informativos. En caso de discrepancia, prevalece la versión en inglés.

## Autor
Kevin-2099
