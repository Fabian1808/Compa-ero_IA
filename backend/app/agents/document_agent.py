from __future__ import annotations

from datetime import datetime

from app.ai.service import AIService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import AgentContext, AgentTask, BaseAgent
from app.connectors.excel import ExcelConnector
from app.services.graph_service import GraphService


class DocumentAgent(BaseAgent):
    """Agent for document generation, extraction, and processing."""

    def __init__(self, db: AsyncSession, user_id: str):
        super().__init__("document_agent", "Document Agent", "Document generation, extraction, and processing")
        self.db = db
        self.user_id = user_id
        self.ai_service = AIService(db, user_id)

    @property
    def capabilities(self) -> list[str]:
        return [
            "document_generation",
            "document_summarization",
            "document_extraction",
            "template_filling",
            "report_generation",
            "excel_automation",
            "meeting_notes_generation",
        ]

    @property
    def required_permissions(self) -> list[str]:
        return ["documents:read", "documents:write", "excel:read", "excel:write", "calendar:read"]

    async def initialize(self, context: AgentContext) -> bool:
        return True

    async def execute(self, task: AgentTask, context: AgentContext) -> dict:
        task_type = task.type

        if task_type == "document_generation":
            return await self._generate_document(task.payload, context)
        elif task_type == "document_summarization":
            return await self._summarize_document(task.payload, context)
        elif task_type == "document_extraction":
            return await self._extract_data(task.payload, context)
        elif task_type == "template_filling":
            return await self._fill_template(task.payload, context)
        elif task_type == "report_generation":
            return await self._generate_report(task.payload, context)
        elif task_type == "excel_automation":
            return await self._excel_automation(task.payload, context)
        elif task_type == "meeting_notes_generation":
            return await self._generate_meeting_notes(task.payload, context)

        return {"error": f"Unknown task type: {task_type}"}

    async def handle_message(self, message, context: AgentContext):
        return None

    async def _generate_document(self, payload: dict, context: AgentContext) -> dict:
        """Generate a document from template or scratch."""
        doc_type = payload.get("type", "memo")  # memo, report, proposal, email, etc.
        topic = payload.get("topic")
        structure = payload.get("structure", [])
        key_points = payload.get("key_points", [])
        tone = payload.get("tone", "professional")
        length = payload.get("length", "medium")  # short, medium, long

        if not topic:
            return {"error": "topic required"}

        prompt = f"""
        Genera un documento {doc_type} sobre: {topic}
        
        Estructura solicitada: {structure if structure else 'Estándar'}
        Puntos clave a incluir: {', '.join(key_points) if key_points else 'Ninguno específico'}
        Tono: {tone}
        Longitud: {length}
        
        El documento debe estar bien estructurado, con encabezados claros y contenido accionable.
        """

        response = await self.ai_service.chat_with_tools(prompt)

        return {
            "type": doc_type,
            "topic": topic,
            "content": response.get("answer", ""),
            "tone": tone,
            "generated_at": datetime.utcnow().isoformat(),
            "word_count": len(response.get("answer", "").split()),
        }

    async def _summarize_document(self, payload: dict, context: AgentContext) -> dict:
        """Summarize a document."""
        content = payload.get("content")
        file_id = payload.get("file_id")
        max_length = payload.get("max_length", 500)

        if file_id:
            # TODO: Extract content from file (PDF, Word, etc.)
            return {"error": "File-based summarization not yet implemented"}

        if not content:
            return {"error": "content or file_id required"}

        prompt = f"""
        Resume el siguiente documento en español, máximo {max_length} palabras:
        
        {content}
        
        Incluye:
        1. Idea principal
        2. Puntos clave (3-5 bullets)
        3. Conclusiones/Acciones
        """

        response = await self.ai_service.chat_with_tools(prompt)

        return {
            "summary": response.get("answer", ""),
            "original_length": len(content.split()),
            "summary_length": len(response.get("answer", "").split()),
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def _extract_data(self, payload: dict, context: AgentContext) -> dict:
        """Extract structured data from document."""
        content = payload.get("content")
        schema = payload.get("schema", {})  # Expected fields

        if not content:
            return {"error": "content required"}

        prompt = f"""
        Extrae la siguiente información estructurada del documento:
        
        Esquema esperado: {schema}
        
        Documento:
        {content}
        
        Devuelve JSON con los campos encontrados. Si un campo no está presente, usa null.
        """

        response = await self.ai_service.chat_with_tools(prompt)

        return {
            "extracted_data": response.get("answer", ""),
            "schema": schema,
            "extracted_at": datetime.utcnow().isoformat(),
        }

    async def _fill_template(self, payload: dict, context: AgentContext) -> dict:
        """Fill a document template with data."""
        template = payload.get("template")
        data = payload.get("data", {})

        if not template:
            return {"error": "template required"}

        # Simple placeholder replacement
        filled = template
        for key, value in data.items():
            placeholder = f"{{{{{key}}}}}"
            filled = filled.replace(placeholder, str(value))

        # Use AI to improve formatting
        prompt = f"""
        Mejora el formato y legibilidad de este documento rellenado:
        
        {filled}
        
        Mantén la estructura pero mejora la redacción donde sea necesario.
        """

        response = await self.ai_service.chat_with_tools(prompt)

        return {
            "filled_template": response.get("answer", filled),
            "fields_filled": len(data),
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def _generate_report(self, payload: dict, context: AgentContext) -> dict:
        """Generate a structured report."""
        report_type = payload.get("report_type", "weekly")  # daily, weekly, monthly, project
        period = payload.get("period")
        data_sources = payload.get("data_sources", [])

        # This would integrate with various data sources
        # For now, generate a template report
        prompt = f"""
        Genera un reporte {report_type} para el período: {period or 'actual'}
        
        Fuentes de datos: {', '.join(data_sources) if data_sources else 'Tareas, Reuniones, Proyectos, Compromisos'}
        
        Estructura sugerida:
        1. Resumen ejecutivo
        2. Métricas clave
        3. Logros del período
        4. Pendientes/Bloqueos
        5. Próximos pasos
        5. Recomendaciones
        """

        response = await self.ai_service.chat_with_tools(prompt)

        return {
            "report_type": report_type,
            "period": period,
            "content": response.get("answer", ""),
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def _excel_automation(self, payload: dict, context: AgentContext) -> dict:
        """Automate Excel operations."""
        action = payload.get("action")  # read, write, import_tasks, export_tasks
        file_id = payload.get("file_id")
        sheet_name = payload.get("sheet_name")

        if not action or not file_id:
            return {"error": "action and file_id required"}

        # Get GraphService for Excel connector
        graph_service = GraphService(self.db)
        from app.models.account import Account
        account = Account()
        account.id = "excel"
        account.user_id = self.user_id

        excel_connector = ExcelConnector(graph_service, account.id, account.user_id)

        if action == "read":
            result = await excel_connector.read_workbook(file_id, sheet_name)
        elif action == "write":
            sheets_data = payload.get("sheets_data", {})
            result = await excel_connector.write_workbook(file_id, sheets_data)
        elif action == "import_tasks":
            column_mapping = payload.get("column_mapping", {})
            header_row = payload.get("header_row", 1)
            result = await excel_connector.import_tasks_from_excel(file_id, sheet_name, column_mapping, header_row)
        elif action == "export_tasks":
            tasks = payload.get("tasks", [])
            column_mapping = payload.get("column_mapping", {})
            result = await excel_connector.export_tasks_to_excel(file_id, sheet_name, tasks, column_mapping)
        elif action == "create":
            name = payload.get("name", "Workbook")
            folder_id = payload.get("folder_id")
            result = await excel_connector.create_workbook(name, folder_id)
        else:
            return {"error": f"Unknown action: {action}"}

        return result

    async def _generate_meeting_notes(self, payload: dict, context: AgentContext) -> dict:
        """Generate meeting notes from calendar event or transcript."""
        meeting_id = payload.get("meeting_id")
        transcript = payload.get("transcript")
        template = payload.get("template", "standard")

        if not meeting_id and not transcript:
            return {"error": "meeting_id or transcript required"}

        if meeting_id and not transcript:
            from app.models.meeting import Meeting
            stmt = select(Meeting).where(Meeting.id == meeting_id)
            result = await self.db.execute(stmt)
            meeting = result.scalar_one_or_none()
            if not meeting:
                return {"error": "Meeting not found"}

            meeting_info = f"""
            Reunión: {meeting.subject}
            Fecha: {meeting.start_at.strftime('%d/%m/%Y %H:%M')}
            Duración: {(meeting.end_at - meeting.start_at).total_seconds() / 60:.0f} min
            Asistentes: {meeting.attendees_json}
            Online: {'Sí' if meeting.is_online else 'No'}
            Enlace: {meeting.meeting_url or 'N/A'}
            """
        else:
            meeting_info = f"Transcripción disponible: {len(transcript)} caracteres"

        prompt = f"""
        Genera notas de reunión estructuradas ({template}):
        
        {meeting_info}
        {f'Transcripción: {transcript}' if transcript else ''}
        
        Estructura:
        1. Información de la reunión
        2. Asistentes
        3. Temas discutidos
        4. Decisiones tomadas
        5. Acciones acordadas (quién, qué, cuándo)
        6. Próximos pasos
        7. Próxima reunión (si aplica)
        """

        response = await self.ai_service.chat_with_tools(prompt)

        return {
            "meeting_id": meeting_id,
            "notes": response.get("answer", ""),
            "template": template,
            "generated_at": datetime.utcnow().isoformat(),
        }
