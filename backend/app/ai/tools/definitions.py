TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_pending_tasks",
            "description": "Obtiene tareas pendientes del usuario con filtros opcionales",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "status": {"type": "array", "items": {"type": "string", "enum": ["pending", "in_progress", "blocked"]}},
                    "limit": {"type": "integer", "default": 20}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_calendar_events",
            "description": "Obtiene eventos del calendario en un rango de fechas",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "format": "date-time"},
                    "end_date": {"type": "string", "format": "date-time"}
                },
                "required": ["start_date", "end_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_emails",
            "description": "Busca correos por query semántica o keywords",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "default": 10},
                    "since_days": {"type": "integer"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_task",
            "description": "Crea una nueva tarea (requiere confirmación del usuario)",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "deadline_at": {"type": "string", "format": "date-time"},
                    "estimated_minutes": {"type": "integer"},
                    "project_id": {"type": "string"},
                    "source_email_id": {"type": "string"}
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "complete_task",
            "description": "Marca una tarea como completada",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string"},
                    "actual_minutes": {"type": "integer"}
                },
                "required": ["task_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "prepare_followup_email",
            "description": "Prepara borrador de seguimiento (NO envía)",
            "parameters": {
                "type": "object",
                "properties": {
                    "to_email": {"type": "string"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"},
                    "original_email_id": {"type": "string"}
                },
                "required": ["to_email", "subject", "body"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "semantic_search",
            "description": "Búsqueda semántica en la memoria del usuario (emails, tareas, compromisos, reuniones, proyectos, seguimientos)",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Consulta en lenguaje natural"},
                    "limit": {"type": "integer", "default": 10},
                    "source_types": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["email", "task", "commitment", "followup", "meeting", "project", "document", "chat"]},
                        "description": "Filtrar por tipo de fuente"
                    }
                },
                "required": ["query"]
            }
        }
    }
]