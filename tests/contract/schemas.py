"""The agreed shape of every API response.

If a developer renames, removes or retypes a field, these schemas fail in CI
before a mobile app or another service breaks in production.
"""

DATETIME = {"type": "string", "format": "date-time"}
NULLABLE_DATE = {"type": ["string", "null"], "format": "date"}
PERSON_REF = {
    "type": "object",
    "required": ["id", "name"],
    "properties": {"id": {"type": "integer"}, "name": {"type": "string"}},
}

ERROR = {
    "type": "object",
    "required": ["error"],
    "additionalProperties": False,
    "properties": {
        "error": {
            "type": "object",
            "required": ["status", "message"],
            "properties": {"status": {"type": "integer"}, "message": {"type": "string"}},
        }
    },
}

USER = {
    "type": "object",
    "required": ["id", "email", "name", "role", "created_at"],
    "additionalProperties": False,
    "properties": {
        "id": {"type": "integer"},
        "email": {"type": "string"},
        "name": {"type": "string"},
        "role": {"enum": ["admin", "member", "viewer"]},
        "created_at": DATETIME,
    },
}

AUTH_RESPONSE = {
    "type": "object",
    "required": ["user", "token"],
    "properties": {"user": USER, "token": {"type": "string", "minLength": 20}},
}

PROJECT = {
    "type": "object",
    "required": ["id", "key", "name", "description", "owner", "members", "is_archived", "created_at"],
    "additionalProperties": False,
    "properties": {
        "id": {"type": "integer"},
        "key": {"type": "string", "pattern": "^[A-Z][A-Z0-9]{1,9}$"},
        "name": {"type": "string"},
        "description": {"type": "string"},
        "owner": PERSON_REF,
        "members": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "name", "email"],
                "properties": {"id": {"type": "integer"}, "name": {"type": "string"}, "email": {"type": "string"}},
            },
        },
        "is_archived": {"type": "boolean"},
        "created_at": DATETIME,
    },
}

ISSUE = {
    "type": "object",
    "required": [
        "id", "key", "project_key", "title", "description", "type", "priority", "status",
        "reporter", "assignee", "due_date", "comment_count", "created_at", "updated_at",
    ],
    "additionalProperties": False,
    "properties": {
        "id": {"type": "integer"},
        "key": {"type": "string", "pattern": "^[A-Z][A-Z0-9]{1,9}-[0-9]+$"},
        "project_key": {"type": "string"},
        "title": {"type": "string"},
        "description": {"type": "string"},
        "type": {"enum": ["task", "bug", "story"]},
        "priority": {"enum": ["lowest", "low", "medium", "high", "highest"]},
        "status": {"enum": ["todo", "in_progress", "in_review", "done"]},
        "reporter": PERSON_REF,
        "assignee": {"oneOf": [{"type": "null"}, PERSON_REF]},
        "due_date": NULLABLE_DATE,
        "comment_count": {"type": "integer", "minimum": 0},
        "created_at": DATETIME,
        "updated_at": DATETIME,
    },
}

COMMENT = {
    "type": "object",
    "required": ["id", "author", "body", "created_at"],
    "additionalProperties": False,
    "properties": {
        "id": {"type": "integer"},
        "author": PERSON_REF,
        "body": {"type": "string", "minLength": 1},
        "created_at": DATETIME,
    },
}

PLAN = {
    "type": "object",
    "required": ["code", "name", "price_monthly", "max_projects"],
    "additionalProperties": False,
    "properties": {
        "code": {"enum": ["free", "standard", "premium"]},
        "name": {"type": "string"},
        "price_monthly": {"type": "integer", "minimum": 0},
        "max_projects": {"type": ["integer", "null"]},
    },
}

SUBSCRIPTION = {
    "type": "object",
    "required": ["plan", "status", "updated_at"],
    "additionalProperties": False,
    "properties": {
        "plan": {"enum": ["free", "standard", "premium"]},
        "status": {"type": "string"},
        "updated_at": DATETIME,
    },
}

PAYMENT = {
    "type": "object",
    "required": ["id", "plan", "amount", "currency", "status", "mock", "created_at"],
    "additionalProperties": False,
    "properties": {
        "id": {"type": "integer"},
        "plan": {"type": "string"},
        "amount": {"type": "integer", "minimum": 0},
        "currency": {"type": "string", "pattern": "^[A-Z]{3}$"},
        "status": {"type": "string"},
        "mock": {"type": "boolean"},
        "created_at": DATETIME,
    },
}

USAGE = {
    "type": "object",
    "required": ["plan", "projects_used", "projects_limit", "projects_remaining"],
    "additionalProperties": False,
    "properties": {
        "plan": {"type": "string"},
        "projects_used": {"type": "integer"},
        "projects_limit": {"type": ["integer", "null"]},
        "projects_remaining": {"type": ["integer", "null"]},
    },
}

HEALTH = {
    "type": "object",
    "required": ["status", "service", "version"],
    "properties": {
        "status": {"const": "ok"},
        "service": {"type": "string"},
        "version": {"type": "string"},
    },
}

READY = {
    "type": "object",
    "required": ["status", "checks"],
    "properties": {
        "status": {"enum": ["ready", "not_ready"]},
        "checks": {
            "type": "object",
            "required": ["database"],
            "additionalProperties": {
                "type": "object",
                "required": ["ok"],
                "properties": {"ok": {"type": "boolean"}},
            },
        },
    },
}


def wrap(key, schema):
    """Response body like {"project": {...}}."""
    return {"type": "object", "required": [key], "properties": {key: schema}}


def wrap_list(key, schema):
    """Response body like {"projects": [{...}, ...]}."""
    return {"type": "object", "required": [key], "properties": {key: {"type": "array", "items": schema}}}
