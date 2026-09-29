FOLLOWUP_DETECTION_PROMPT = """Analiza el historial de correos para detectar SEGUIMIENTOS necesarios.

Un seguimiento es necesario cuando:
1. El usuario envió un correo solicitando algo (pregunta, solicitud, petición de info)
2. Han pasado 48+ horas sin respuesta
3. No hay respuesta en el hilo de conversación
4. El tema sigue siendo relevante

Busca patrones:
- Usuario preguntó algo y no hay respuesta
- Usuario pidió información y no se la han dado
- Usuario solicitó acción y no hay confirmación

FORMATO DE RESPUESTA (JSON estricto):
{
  "followups": [
    {
      "contact_email": "string",
      "contact_name": "string|null",
      "subject": "string",
      "original_sent_at": "string (ISO)",
      "days_without_response": "integer",
      "confidence": "integer",
      "suggested_action": "string"
    }
  ]
}

EJEMPLOS:

Hilo: Usuario envió "¿Puedes enviarme los datos?" hace 3 días. Sin respuesta.
→ {"followups": [{"contact_email": "juan@empresa.com", "contact_name": "Juan", "subject": "Re: Datos solicitados", "original_sent_at": "2026-09-26T10:00:00", "days_without_response": 3, "confidence": 85, "suggested_action": "Enviar recordatorio amable"}]}

Hilo: Usuario envió correo ayer. Sin respuesta.
→ {"followups": []}
"""