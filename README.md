# 📑 Contract Analyzer / Analizador de Contratos

Aplicación avanzada de análisis contractual construida con **Python y Gradio**. Permite analizar contratos automáticamente, detectar cláusulas relevantes, identificar indicadores de riesgo, extraer información clave, comparar versiones y generar informes visuales y exportables.

---

## 🚀 Funcionalidades

### 🌍 Análisis multi-idioma

* Detección automática o selección manual del idioma.
* Idiomas compatibles:

  * 🇪🇸 Español
  * 🇬🇧 Inglés
  * 🇫🇷 Francés
  * 🇵🇹 Portugués

---

### 📂 Soporte de archivos

Puedes analizar contratos desde:

* `.txt`
* `.pdf`
* `.docx`

También puedes pegar el texto directamente en la aplicación.

El soporte de PDF y Word utiliza dependencias opcionales para mantener un funcionamiento flexible.

---

## 📊 Dashboard de análisis

La aplicación genera un dashboard visual con:

* 📊 Score global de riesgo.
* 📈 Barra visual de riesgo.
* 📋 Checklist legal.
* 📄 Estadísticas del documento.
* 👥 Partes identificadas.
* 📅 Fechas y plazos.
* 💰 Montos detectados.
* 🚫 Cláusulas potencialmente abusivas.
* 🧩 Cláusulas clasificadas.
* 🚨 Riesgos detectados.

---

## 🧩 Extracción de cláusulas

El sistema identifica automáticamente diferentes categorías contractuales:

| Categoría           | Indicadores                                          |
| ------------------- | ---------------------------------------------------- |
| 💰 Pagos            | Pagos, honorarios, tarifas, facturas, remuneraciones |
| ⚠️ Penalizaciones   | Penalizaciones, multas, sanciones, intereses, daños  |
| 📌 Obligaciones     | Deberes, compromisos, cumplimiento, entrega          |
| 🔒 Confidencialidad | Información confidencial, NDA, secretos              |
| ❌ Terminación       | Terminación, cancelación, rescisión, expiración      |

Cada resultado incluye una referencia para facilitar su localización:

```text
[Ref 12]
```

---

## 🚨 Detección y clasificación de riesgos

Los riesgos encontrados se clasifican automáticamente según su severidad:

* 🟢 **Bajo**
* 🟡 **Moderado**
* 🔴 **Alto**
* 💀 **Crítico**

El sistema genera un **score global de riesgo** basado en los riesgos detectados.

### Ponderación

| Nivel       | Peso |
| ----------- | ---: |
| 🟢 Bajo     |    1 |
| 🟡 Moderado |    2 |
| 🔴 Alto     |    3 |
| 💀 Crítico  |    4 |

El score se utiliza como indicador heurístico para ayudar a priorizar la revisión.

---

## 🚫 Detección de cláusulas potencialmente abusivas

La aplicación busca patrones contractuales que pueden requerir una revisión adicional, como:

* `a sola discreción`
* `sin previo aviso`
* `en cualquier momento y sin causa`
* `prórroga automática`
* `renuncia irrevocable`
* `sin responsabilidad alguna`
* `según estime conveniente`
* `sin limitación alguna`
* `sin necesidad de notificación`
* `modificar en cualquier momento`

> La detección de un patrón **no significa que la cláusula sea legalmente abusiva**. El resultado funciona como indicador para revisión.

---

## 📅 Extracción de información clave

El sistema detecta automáticamente:

### 📅 Fechas y plazos

* Fechas en diferentes formatos.
* Días.
* Meses.
* Años.
* Plazos en días naturales.
* Plazos en días laborables.
* Fechas en inglés.

### 💰 Montos

Detecta cantidades asociadas a monedas como:

* EUR
* USD
* MXN
* COP
* ARS
* GBP
* BRL
* €
* $
* £

### 👥 Partes

Intenta identificar las partes mencionadas en estructuras contractuales como:

```text
en adelante denominado...
hereinafter referred to as...
entre X y Y...
between X and Y...
```

---

## 📋 Checklist legal

El sistema genera automáticamente un checklist de las categorías contractuales detectadas.

Ejemplo:

```text
✅ Pagos
✅ Obligaciones
✗ Confidencialidad
✅ Terminación
✗ Penalizaciones
```

Esto permite realizar una comprobación rápida de la presencia de determinadas categorías.

---

## 📈 Visualización de datos

La aplicación genera gráficos automáticamente.

### 📊 Cláusulas por tipo

Gráfico de barras que muestra cuántas cláusulas fueron identificadas en cada categoría.

### 🥧 Distribución de riesgos

Gráfico circular que muestra la distribución entre:

* Bajo
* Moderado
* Alto
* Crítico

---

# 🔍 Comparador de contratos

Incluye un comparador avanzado para analizar dos versiones de un contrato.

### Funcionalidades

* 📄 Comparación lado a lado.
* 📊 Porcentaje de similitud.
* ➕ Líneas añadidas.
* ➖ Líneas eliminadas.
* ✏️ Líneas modificadas.
* 🔎 Resaltado de cambios a nivel de palabras.
* ☑️ Opción **Mostrar solo diferencias**.

Ejemplo de métricas:

```text
📊 Similitud: 87.5%
➕ Añadidas: 4
➖ Eliminadas: 2
✏️ Modificadas: 7
```

La comparación utiliza `difflib.SequenceMatcher`.

---

# 📤 Exportación

Los resultados del análisis pueden exportarse en:

* 📄 **HTML**
* 📊 **CSV**

### HTML

Genera un informe HTML a partir del informe estructurado.

### CSV

Genera datos estructurados con:

* Tipo
* Referencia
* Texto
* Nivel de riesgo

---

# 📝 Informe estructurado

El análisis genera un informe que puede incluir:

* 📝 Resumen ejecutivo.
* 🌍 Idioma detectado.
* 📊 Estadísticas del documento.
* 👥 Partes identificadas.
* 📅 Fechas y plazos.
* 💰 Montos.
* 🧩 Cláusulas clasificadas.
* 🚫 Cláusulas potencialmente abusivas.
* 🚨 Riesgos.
* 📋 Checklist legal.
* 📊 Score global.

---

# ⚡ Uso

## 🔍 Analizar un contrato

1. Ejecuta la aplicación.
2. Sube un archivo `.txt`, `.pdf` o `.docx`.
3. O pega directamente el texto.
4. Selecciona el idioma o utiliza `Auto`.
5. Pulsa **Analizar**.
6. Consulta:

   * Dashboard
   * Informe
   * Gráficos

---

## 🔍 Comparar contratos

1. Abre la pestaña **Comparar Contratos**.
2. Introduce el **Contrato A**.
3. Introduce el **Contrato B**.
4. Activa opcionalmente **Mostrar solo diferencias**.
5. Pulsa **Comparar**.
6. Revisa las modificaciones detectadas.

---

# 🛠️ Tecnologías utilizadas

* 🐍 **Python 3.10+**
* 🎨 **Gradio**
* 🌍 **langdetect**
* 🔎 **Regex**
* 🔀 **difflib / SequenceMatcher**
* 📊 **Matplotlib**
* 📄 **pdfplumber** — opcional
* 📝 **python-docx** — opcional

---

# 📦 Instalación

Clona el repositorio:

```bash
git clone https://github.com/Kevin-2099/Analizador-de-contratos
cd Analizador-de-contratos
```

Instala las dependencias:

```bash
pip install -r requirements.txt
```

Ejecuta la aplicación:

```bash
python app.py
```

---

# 🧠 Metodología

Contract Analyzer utiliza principalmente técnicas de procesamiento de texto basadas en reglas:

* 🔎 Keywords específicas por idioma.
* 🧩 Expresiones regulares.
* 📋 Patrones contractuales.
* 🚨 Clasificación heurística de riesgos.
* 📅 Extracción mediante expresiones regulares.
* 💰 Detección de cantidades monetarias.
* 👥 Detección de partes.
* 🔀 Comparación mediante `SequenceMatcher`.

No depende de un modelo de lenguaje externo para realizar el análisis principal.

---

# ⚠️ Limitaciones

Los resultados son **indicadores automáticos** y deben revisarse antes de tomar decisiones.

El sistema puede producir:

* Falsos positivos.
* Falsos negativos.
* Extracciones incorrectas.
* Cláusulas no detectadas debido a diferencias de redacción.
* Identificación imperfecta de nombres, fechas o cantidades.

El **score de riesgo no constituye una valoración jurídica oficial**.

Asimismo, detectar una cláusula potencialmente abusiva no significa necesariamente que dicha cláusula sea ilegal o jurídicamente abusiva.

---

# 🎯 Casos de uso

La herramienta está diseñada para facilitar:

* 🔎 Revisión preliminar de contratos.
* 📑 Lectura rápida de documentos extensos.
* 🚨 Identificación inicial de riesgos.
* 📋 Comprobación de cláusulas.
* 📊 Priorización de contratos para revisión.
* 🔀 Comparación de versiones.
* 💰 Extracción de importes.
* 📅 Extracción de fechas y plazos.
* 👥 Identificación de partes.

---

# 💡 Aviso

**Contract Analyzer no sustituye el asesoramiento legal profesional.**

La herramienta está diseñada como apoyo para análisis y revisión preliminar de documentos contractuales.

Para decisiones jurídicas, financieras o comerciales importantes, se recomienda consultar con un profesional cualificado.

---

# 📄 Licencia

Este proyecto se distribuye bajo una **licencia propietaria con acceso al código (source-available)**.

El código fuente se pone a disposición únicamente para fines de **visualización, evaluación y aprendizaje**.

❌ No está permitido copiar, modificar, redistribuir, sublicenciar ni crear obras derivadas del software o de su código fuente sin autorización escrita expresa del titular de los derechos.

❌ El uso comercial del software, incluyendo su oferta como servicio (**SaaS**), su integración en productos comerciales o su uso en entornos de producción, requiere un **acuerdo de licencia comercial independiente**.

📌 El texto **legalmente vinculante** de la licencia es la versión en inglés incluida en el archivo `LICENSE`.

Se proporciona una traducción al español en `LICENSE_ES.md` únicamente con fines informativos. En caso de discrepancia, prevalece la versión en inglés.

---

# 👤 Autor

**Kevin-2099**
