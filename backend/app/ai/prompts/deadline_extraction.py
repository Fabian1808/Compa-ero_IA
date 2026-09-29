DEADLINE_EXTRACTION_PROMPT = """Analiza el correo para detectar DEADLINES (fechas límite) explícitas mencionadas en el correo.

Busca patrones como:
- "antes del viernes", "para el viernes", "el viernes como máximo"
- "antes de las 4pm", "para las 16:00"
- "para mañana", "mañana a primera hora"
- "la próxima semana", "el lunes"
- "antes de fin de mes", "para el 30 de septiembre"
- "deadline", "fecha límite", "vence el"

Extrae SOLO deadlines que afecten a tareas del usuario.
Si el correo dice "necesito esto para el viernes" y el usuario es el destinatario, es un deadline para él.
Si el usuario dice "te lo entrego el viernes", es un deadline autoimpuesto (compromiso, no deadline externo).

FORMATO DE RESPUESTA (JSON estricto):
{
  "deadlines": [
    {
      "description": "string",
      "deadline_iso": "string",
      "confidence": "integer",
      "evidence_quote": "string",
      "is_external": "boolean"
    }
  ]
}

EJEMPLOS:

Correo: "Necesito el reporte antes del viernes a las 4pm."
→ {"deadlines": [{"description": "Entregar reporte", "deadline_iso": "2026-10-04T16:00:00", "confidence": 95, "evidence_quote": "antes del viernes a las 4pm", "is_external": true}]}

Correo: "El deadline es el 30 de septiembre."
→ {"deadlines": [{"description": "Entregar trabajo", "deadline_iso": "2026-09-30T23:59:00", "confidence": 90, "evidence_quote": "deadline es el 30 de septiembre", "is_external": true}]}

Correo: "Te lo envío el viernes." (enviado por usuario)
→ {"deadlines": []}
"""