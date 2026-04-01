"""
Prompt templates for the Hugging Face LLM study plan generator.
Designed for google/flan-t5-large and Mistral-7B-Instruct.
"""

from datetime import date
from typing import List, Optional


def build_study_plan_prompt(
    branch: str,
    subjects: List[str],
    topics_map: dict,
    prep_type: str,
    daily_hours: float,
    week_number: int,
    start_date: str,
    days_count: int = 7,
    coaching_start: Optional[str] = None,
    coaching_end: Optional[str] = None,
    study_slots: Optional[list] = None,
    completed_topics: Optional[List[str]] = None,
    skipped_topics: Optional[List[str]] = None,
) -> str:
    """
    Build a structured prompt for generating a weekly GATE study plan.
    Returns a prompt string optimized for JSON output.
    """
    completed_str = ""
    if completed_topics:
        completed_str = f"\nAlready completed topics (do NOT repeat): {', '.join(completed_topics)}"

    skipped_str = ""
    if skipped_topics:
        skipped_str = f"\nPreviously skipped topics (prioritize these): {', '.join(skipped_topics)}"

    schedule_info = ""
    if prep_type == "coaching":
        if study_slots:
            slots_str = ", ".join(str(s) for s in study_slots)
        else:
            slots_str = f"before {coaching_start} and after {coaching_end}"
        schedule_info = f"""
Student attends coaching from {coaching_start} to {coaching_end}.
DO NOT schedule any tasks between {coaching_start} and {coaching_end} — those are coaching hours.
Available self-study windows: {slots_str}
Plan ALL tasks strictly within these windows only."""
    else:
        schedule_info = f"""
Student is self-studying with {daily_hours} hours available per day.
Distribute study time evenly across the day starting from morning."""

    topics_detail = ""
    for subj in subjects:
        if subj in topics_map:
            topics = topics_map[subj].get("topics", [])
            weight = topics_map[subj].get("weight", 10)
            topics_detail += f"\n  {subj} (weightage: {weight}%): {', '.join(topics)}"

    prompt = f"""Generate a detailed {days_count}-day GATE {branch} study plan for Week {week_number} starting {start_date}.

Student Profile:
- Branch: {branch}
- Preparation type: {prep_type}
- Subjects to cover: {', '.join(subjects)}
{schedule_info}
{completed_str}
{skipped_str}

Subject Details:{topics_detail}

Requirements:
1. Create exactly {days_count} days of study tasks
2. Each day should have 3-5 tasks
3. Include revision sessions every 3rd day
4. Add one mock test or practice session per week
5. Allocate time based on subject weightage
6. Prioritize skipped topics if any
7. Include specific timings for each task
8. Balance difficult and easier subjects each day

Output STRICT JSON format:
[
  {{
    "day": "Day 1",
    "date": "{start_date}",
    "tasks": [
      {{
        "subject": "Subject Name",
        "topic": "Topic Name",
        "subtopic": "Specific subtopic",
        "duration": "2h",
        "timing": "9:00 AM - 11:00 AM",
        "task_type": "study"
      }}
    ]
  }}
]

task_type must be one of: study, revision, mock_test, practice
Output ONLY the JSON array, no other text."""

    return prompt


def build_reschedule_prompt(
    skipped_tasks: List[dict],
    remaining_days: int,
    daily_hours: float,
    existing_tasks: List[dict],
) -> str:
    """
    Build a prompt for rescheduling skipped/pending tasks.
    """
    skipped_str = "\n".join(
        f"- {t['subject']}: {t['topic']} ({t['duration']})" for t in skipped_tasks
    )
    existing_str = "\n".join(
        f"- Day {t['day']}: {t['subject']} - {t['topic']} ({t['duration']})"
        for t in existing_tasks[:10]  # Limit context
    )

    prompt = f"""Reschedule these skipped GATE study tasks into the remaining {remaining_days} days.

Skipped tasks to reschedule:
{skipped_str}

Already scheduled tasks (do not conflict):
{existing_str}

Available hours per day: {daily_hours}

Requirements:
1. Spread skipped tasks across remaining days
2. Don't overload any single day (max {daily_hours}h)
3. Maintain subject variety each day
4. Prioritize topics that were skipped

Output STRICT JSON array of rescheduled tasks:
[
  {{
    "subject": "Subject Name",
    "topic": "Topic Name",
    "duration": "2h",
    "timing": "suggested time",
    "scheduled_date": "YYYY-MM-DD",
    "task_type": "study"
  }}
]

Output ONLY the JSON array."""

    return prompt


def build_weak_topic_prompt(
    branch: str,
    weak_subjects: List[dict],
    available_hours: float,
) -> str:
    """
    Build a prompt for generating focused revision on weak topics.
    """
    weak_str = "\n".join(
        f"- {s['subject']}: {s['topic']} (completion: {s['completion_rate']}%)"
        for s in weak_subjects
    )

    prompt = f"""Create a focused revision plan for weak GATE {branch} topics.

Weak areas identified:
{weak_str}

Available time: {available_hours} hours

Requirements:
1. Prioritize lowest completion rate topics
2. Include practice problems for each topic
3. Add concept revision before practice
4. Suggest specific resources

Output STRICT JSON:
[
  {{
    "subject": "Subject",
    "topic": "Topic",
    "revision_strategy": "Brief strategy",
    "duration": "1.5h",
    "task_type": "revision"
  }}
]

Output ONLY the JSON array."""

    return prompt
