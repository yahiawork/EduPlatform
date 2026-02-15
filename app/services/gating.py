from ..models import Progress, Exercise, Lesson
from ..extensions import db


def _ordered_exercise_ids() -> list[int]:
    """Return exercise IDs in the learning sequence.

    Order: lesson.order -> exercise.order -> exercise.id (stable tie-breaker)
    """
    rows = (
        Exercise.query
        .join(Lesson, Exercise.lesson_id == Lesson.id)
        .order_by(Lesson.order.asc(), Exercise.order.asc(), Exercise.id.asc())
        .with_entities(Exercise.id)
        .all()
    )
    return [r[0] for r in rows]


def _index_of(exercise_ids: list[int], exercise_id: int) -> int:
    try:
        return exercise_ids.index(exercise_id)
    except ValueError:
        return -1

def get_progress(student_id: int) -> Progress:
    p = Progress.query.filter_by(student_id=student_id).first()
    if not p:
        p = Progress(student_id=student_id, highest_exercise_id=0)
        db.session.add(p)
        db.session.commit()
    return p

def can_open_exercise(student_id: int, exercise_id: int) -> bool:
    p = get_progress(student_id)

    ordered = _ordered_exercise_ids()
    if not ordered:
        return False

    target_idx = _index_of(ordered, exercise_id)
    if target_idx == -1:
        return False

    passed_idx = _index_of(ordered, p.highest_exercise_id) if p.highest_exercise_id else -1
    return target_idx <= (passed_idx + 1)

def mark_passed(student_id: int, exercise_id: int) -> None:
    p = get_progress(student_id)

    ordered = _ordered_exercise_ids()
    if not ordered:
        return

    new_idx = _index_of(ordered, exercise_id)
    if new_idx == -1:
        return

    cur_idx = _index_of(ordered, p.highest_exercise_id) if p.highest_exercise_id else -1
    if new_idx > cur_idx:
        p.highest_exercise_id = exercise_id
        db.session.commit()


def progress_stats(student_id: int) -> tuple[int, int]:
    """(passed_count, total_count) in the ordered sequence."""
    p = get_progress(student_id)
    ordered = _ordered_exercise_ids()
    total = len(ordered)
    if total == 0:
        return (0, 0)
    passed_idx = _index_of(ordered, p.highest_exercise_id) if p.highest_exercise_id else -1
    return (max(passed_idx + 1, 0), total)
