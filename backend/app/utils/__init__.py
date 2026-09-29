def generate_uuid() -> str:
    import uuid
    return str(uuid.uuid4())


def now_utc() -> datetime:
    from datetime import datetime
    return datetime.utcnow()