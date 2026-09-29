from app.ai.prompts.task_extraction import TASK_EXTRACTION_PROMPT
from app.ai.prompts.commitment_extraction import COMMITMENT_EXTRACTION_PROMPT
from app.ai.prompts.deadline_extraction import DEADLINE_EXTRACTION_PROMPT
from app.ai.prompts.followup_detection import FOLLOWUP_DETECTION_PROMPT
from app.ai.prompts.next_task_recommendation import NEXT_TASK_RECOMMENDATION_PROMPT

__all__ = [
    "TASK_EXTRACTION_PROMPT",
    "COMMITMENT_EXTRACTION_PROMPT",
    "DEADLINE_EXTRACTION_PROMPT",
    "FOLLOWUP_DETECTION_PROMPT",
    "NEXT_TASK_RECOMMENDATION_PROMPT",
]