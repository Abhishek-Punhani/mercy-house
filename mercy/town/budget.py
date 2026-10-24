"""Public reply limits. Official judging is always capped at forty replies."""
from .tasks import TASKS


def reply_limit(task, practice=False):
    details=TASKS.get(task,{}) if isinstance(task,str) else (task or {})
    return 100 if practice and details.get('difficulty') in ('intermediate','advanced') else 40
