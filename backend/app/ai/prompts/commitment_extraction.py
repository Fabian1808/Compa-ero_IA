COMMITMENT_EXTRACTION_PROMPT = """Analiza el correo para detectar COMPROMISOS que el USUARIO (remitente O destinatario) ha hecho explícitamente.

Busca patrones de compromiso propio:
- "te lo envío mañana", "te lo paso mañana"
- "lo reviso esta tarde", "lo reviso hoy"
- "el viernes te paso el reporte", "para el viernes te lo entrego"
- "te confirmo luego", "te confirmo mañana"
- "déjame revisarlo", "lo miro y te digo"
- "me comprometo a", "me encargo de"

NO inventes compromisos. Solo extrae los explícitos y claros.
Distingue si el compromiso es DEL USUARIO (remitente) o HACIA EL USUARIO (destinatario).
Solo nos interesan los compromisos DEL USUARIO (que él debe cumplir).

FORMATO DE RESPUESTA (JSON estricto):
{
  "commitments": [
    {
      "description": "string",
      "due_date_iso": "string|null",
      "confidence": "integer",
      "evidence_quote": "string",
      "is_user_commitment": "boolean"
    }
  ]
}

EJEMPLOS:

Correo (enviado por usuario): "Te lo envío mañana por la mañana."
→ {"commitments": [{"description": "Enviar documento a Juan", "due_date_iso": "2026-09-30T12:00:00", "confidence": 90, "evidence_quote": "Te lo envío mañana por la mañana", "is_user_commitment": true}]}

Correo (recibido por usuario): "Te lo envío mañana."
→ {"commitments": []}

Correo (enviado por usuario): "Lo reviso esta tarde y te confirmo."
→ {"commitments": [{"description": "Revisar documento y confirmar", "due_date_iso": "2026-09-29T18:00:00", "confidence": 85, "evidence_quote": "Lo reviso esta tarde y te confirmo", "is_user_commitment": true}]}

Correo: "Gracias por el archivo."
→ {"commitments": []}
"""