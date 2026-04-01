"""
AI-powered study plan generation service.
Orchestrates prompt building, LLM inference, and plan structuring.
"""

import json
import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.ai.hf_model_loader import get_model_loader, parse_json_response
from app.ai.prompt_templates import (
    build_reschedule_prompt,
    build_study_plan_prompt,
    build_weak_topic_prompt,
)
from app.utils.gate_data import get_subjects_for_branch

logger = logging.getLogger(__name__)


class PlannerService:
    """
    Generates, validates, and structures study plans using HF LLMs.
    Includes fallback plan generation when LLM output is unreliable.
    """

    def __init__(self):
        self.model = get_model_loader()

    async def generate_weekly_plan(
        self,
        branch: str,
        subjects: List[str],
        prep_type: str,
        daily_hours: float,
        week_number: int,
        start_date: date,
        coaching_start: Optional[str] = None,
        coaching_end: Optional[str] = None,
        study_slots: Optional[list] = None,
        completed_topics: Optional[List[str]] = None,
        skipped_topics: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate a full weekly study plan.
        Falls back to rule-based generation if LLM fails.
        """
        # Get topic data for the branch
        all_subjects = get_subjects_for_branch(branch)

        # Filter to only requested subjects
        topics_map = {
            s: all_subjects[s] for s in subjects if s in all_subjects
        }

        # Build prompt
        prompt = build_study_plan_prompt(
            branch=branch,
            subjects=subjects,
            topics_map=topics_map,
            prep_type=prep_type,
            daily_hours=daily_hours,
            week_number=week_number,
            start_date=start_date.isoformat(),
            coaching_start=coaching_start,
            coaching_end=coaching_end,
            study_slots=study_slots,
            completed_topics=completed_topics,
            skipped_topics=skipped_topics,
        )

        try:
            # Generate via LLM
            raw_output = await self.model.generate(prompt, temperature=0.3)
            plan_data = parse_json_response(raw_output)

            if plan_data and isinstance(plan_data, list) and len(plan_data) > 0:
                # Validate and enrich the plan
                validated = self._validate_plan(plan_data, start_date, daily_hours)
                if coaching_start and coaching_end:
                    validated = self._fix_coaching_timings(validated, coaching_start, coaching_end)
                return validated
        except Exception as e:
            logger.error(f"LLM plan generation failed: {e}")

        # Fallback: rule-based plan generation
        logger.info("Using fallback rule-based plan generation")
        return self._generate_fallback_plan(
            subjects=subjects,
            topics_map=topics_map,
            daily_hours=daily_hours,
            week_number=week_number,
            start_date=start_date,
            prep_type=prep_type,
            coaching_start=coaching_start,
            coaching_end=coaching_end,
        )

    async def reschedule_tasks(
        self,
        skipped_tasks: List[dict],
        remaining_days: int,
        daily_hours: float,
        existing_tasks: List[dict],
    ) -> List[dict]:
        """Reschedule skipped tasks using LLM or rule-based logic."""
        prompt = build_reschedule_prompt(
            skipped_tasks=skipped_tasks,
            remaining_days=remaining_days,
            daily_hours=daily_hours,
            existing_tasks=existing_tasks,
        )

        try:
            raw_output = await self.model.generate(prompt, temperature=0.2)
            result = parse_json_response(raw_output)
            if result and isinstance(result, list):
                return result
        except Exception as e:
            logger.error(f"LLM rescheduling failed: {e}")

        # Fallback: distribute evenly
        return self._fallback_reschedule(skipped_tasks, remaining_days, daily_hours)

    async def get_weak_topic_plan(
        self,
        branch: str,
        weak_subjects: List[dict],
        available_hours: float,
    ) -> List[dict]:
        """Generate a focused revision plan for weak topics."""
        prompt = build_weak_topic_prompt(branch, weak_subjects, available_hours)

        try:
            raw_output = await self.model.generate(prompt, temperature=0.2)
            result = parse_json_response(raw_output)
            if result and isinstance(result, list):
                return result
        except Exception as e:
            logger.error(f"LLM weak topic plan failed: {e}")

        return []

    # ── Plan Validation ──────────────────────────────────────
    def _validate_plan(
        self,
        plan: List[dict],
        start_date: date,
        daily_hours: float,
    ) -> List[dict]:
        """Validate and fix the LLM-generated plan structure."""
        validated = []
        current_date = start_date

        for i, day in enumerate(plan):
            day_entry = {
                "day": day.get("day", f"Day {i + 1}"),
                "date": current_date.isoformat(),
                "tasks": [],
            }

            tasks = day.get("tasks", [])
            total_minutes = 0

            for task in tasks:
                duration_str = task.get("duration", "1h")
                minutes = self._parse_duration(duration_str)
                total_minutes += minutes

                day_entry["tasks"].append({
                    "subject": task.get("subject", "General"),
                    "topic": task.get("topic", "Review"),
                    "subtopic": task.get("subtopic"),
                    "duration": duration_str,
                    "timing": task.get("timing", ""),
                    "task_type": task.get("task_type", "study"),
                })

            # Cap total hours
            if total_minutes > daily_hours * 60 * 1.2:
                logger.warning(
                    f"Day {i+1} exceeds daily hours ({total_minutes}m > {daily_hours*60}m)"
                )

            day_entry["total_hours"] = round(total_minutes / 60, 1)
            validated.append(day_entry)
            current_date += timedelta(days=1)

        return validated

    def _fix_coaching_timings(
        self, plan: List[dict], coaching_start: str, coaching_end: str
    ) -> List[dict]:
        """Reassign tasks that fall inside coaching hours to proper slots outside."""
        from datetime import datetime as dt, timedelta as td

        fmt_candidates = ["%I:%M %p", "%H:%M", "%I %p"]

        def parse_time(t: str):
            for fmt in fmt_candidates:
                try:
                    return dt.strptime(t.strip(), fmt)
                except ValueError:
                    continue
            return None

        def fmt_time(t: dt) -> str:
            return t.strftime("%-I:%M %p") if hasattr(t, 'strftime') else str(t)

        cs = parse_time(coaching_start)
        ce = parse_time(coaching_end)
        if not cs or not ce:
            return plan

        # Available windows: before coaching and after coaching
        day_start = parse_time("5:30 AM")
        day_end = parse_time("10:00 PM")

        # Build a list of free slots: [(window_start, window_end), ...]
        free_windows = []
        if day_start < cs:
            free_windows.append((day_start, cs))
        if ce < day_end:
            free_windows.append((ce, day_end))

        for day in plan:
            # Track current position in free windows per day
            window_idx = 0
            if free_windows:
                cursor = free_windows[0][0]

            for task in day.get("tasks", []):
                timing = task.get("timing", "")
                needs_reassign = False

                if timing:
                    start_part = timing.split("-")[0].strip()
                    task_start = parse_time(start_part)
                    if task_start and cs <= task_start < ce:
                        needs_reassign = True
                else:
                    needs_reassign = True

                if needs_reassign and free_windows:
                    duration_mins = self._parse_duration(task.get("duration", "1h"))
                    task_dur = td(minutes=duration_mins)

                    # Advance cursor to next window if current is exhausted
                    while window_idx < len(free_windows):
                        win_start, win_end = free_windows[window_idx]
                        if cursor < win_start:
                            cursor = win_start
                        if cursor + task_dur <= win_end:
                            break
                        window_idx += 1
                        if window_idx < len(free_windows):
                            cursor = free_windows[window_idx][0]

                    if window_idx < len(free_windows):
                        slot_end = cursor + task_dur
                        task["timing"] = f"{fmt_time(cursor)} - {fmt_time(slot_end)}"
                        cursor = slot_end + td(minutes=10)  # 10-min gap

        return plan

    def _parse_duration(self, duration_str: str) -> int:
        """Parse duration string like '2h', '90m', '1.5h' into minutes."""
        import re
        duration_str = str(duration_str).strip().lower()

        # Match hours
        h_match = re.search(r"(\d+\.?\d*)\s*h", duration_str)
        m_match = re.search(r"(\d+)\s*m", duration_str)

        minutes = 0
        if h_match:
            minutes += int(float(h_match.group(1)) * 60)
        if m_match:
            minutes += int(m_match.group(1))

        return minutes if minutes > 0 else 60  # Default 1 hour

    # ── Fallback Plan Generator ──────────────────────────────
    def _generate_fallback_plan(
        self,
        subjects: List[str],
        topics_map: dict,
        daily_hours: float,
        week_number: int,
        start_date: date,
        prep_type: str,
        coaching_start: Optional[str] = None,
        coaching_end: Optional[str] = None,
    ) -> List[dict]:
        """
        Rule-based fallback plan when LLM generation fails.
        Distributes topics across 7 days with proper pacing.
        """
        plan = []
        current_date = start_date

        # Flatten all topics with weights
        all_topics = []
        for subj in subjects:
            if subj in topics_map:
                weight = topics_map[subj].get("weight", 10)
                for topic in topics_map[subj].get("topics", []):
                    all_topics.append({
                        "subject": subj,
                        "topic": topic,
                        "weight": weight,
                    })

        # Calculate topic offset for this week
        offset = ((week_number - 1) * 7 * 3) % max(len(all_topics), 1)

        # Time slots based on prep type
        if prep_type == "coaching" and coaching_start and coaching_end:
            # Only slots OUTSIDE coaching hours
            base_slots = [
                {"start": "5:30 AM", "end": coaching_start},   # before coaching
                {"start": coaching_end, "end": "10:00 PM"},    # after coaching
            ]
        else:
            base_slots = self._generate_time_slots(daily_hours)

        for day_num in range(7):
            day_tasks = []
            available_minutes = int(daily_hours * 60)
            task_index = 0

            # Add revision task every 3rd day
            is_revision_day = (day_num + 1) % 3 == 0
            # Add mock test on day 6 or 7
            is_mock_day = day_num >= 5

            if is_revision_day:
                rev_minutes = min(60, available_minutes)
                day_tasks.append({
                    "subject": subjects[day_num % len(subjects)],
                    "topic": "Revision - Previous Topics",
                    "subtopic": "Review notes and solve problems",
                    "duration": f"{rev_minutes}m",
                    "timing": base_slots[0]["start"] if base_slots else "",
                    "task_type": "revision",
                })
                available_minutes -= rev_minutes

            if is_mock_day and day_num == 6:
                mock_minutes = min(90, available_minutes)
                day_tasks.append({
                    "subject": "All Subjects",
                    "topic": f"Mock Test - Week {week_number}",
                    "subtopic": "Full-length practice test",
                    "duration": f"{mock_minutes}m",
                    "timing": base_slots[-1]["start"] if base_slots else "",
                    "task_type": "mock_test",
                })
                available_minutes -= mock_minutes

            # Fill remaining time with study tasks
            topics_per_day = max(2, min(4, available_minutes // 60))
            for t in range(topics_per_day):
                if available_minutes <= 0:
                    break

                idx = (offset + day_num * topics_per_day + t) % max(len(all_topics), 1)
                if idx < len(all_topics):
                    topic_entry = all_topics[idx]
                    task_minutes = min(
                        int(available_minutes / max(1, topics_per_day - t)),
                        120,
                    )
                    slot_idx = min(t, len(base_slots) - 1)

                    day_tasks.append({
                        "subject": topic_entry["subject"],
                        "topic": topic_entry["topic"],
                        "subtopic": None,
                        "duration": f"{task_minutes}m",
                        "timing": base_slots[slot_idx]["start"] if slot_idx < len(base_slots) else "",
                        "task_type": "study",
                    })
                    available_minutes -= task_minutes

            total_hours = round(
                sum(self._parse_duration(t["duration"]) for t in day_tasks) / 60, 1
            )

            plan.append({
                "day": f"Day {day_num + 1}",
                "date": current_date.isoformat(),
                "tasks": day_tasks,
                "total_hours": total_hours,
            })
            current_date += timedelta(days=1)

        return plan

    def _generate_time_slots(self, daily_hours: float) -> list:
        """Generate evenly spaced time slots for self-study."""
        slots = []
        hour = 9  # Start at 9 AM
        remaining = daily_hours

        while remaining > 0:
            block = min(2.0, remaining)
            end_hour = hour + block
            start_str = f"{int(hour)}:{'00' if hour % 1 == 0 else '30'} {'AM' if hour < 12 else 'PM'}"
            slots.append({"start": start_str, "end": ""})
            hour = end_hour + 0.5  # 30-min break
            remaining -= block

            # Skip lunch
            if 12 <= hour <= 13:
                hour = 14

        return slots

    def _fallback_reschedule(
        self,
        skipped_tasks: List[dict],
        remaining_days: int,
        daily_hours: float,
    ) -> List[dict]:
        """Simple round-robin rescheduling of skipped tasks."""
        if remaining_days <= 0:
            return []

        tasks_per_day = max(1, len(skipped_tasks) // remaining_days)
        result = []
        today = date.today()

        for i, task in enumerate(skipped_tasks):
            day_offset = i // tasks_per_day
            if day_offset >= remaining_days:
                day_offset = remaining_days - 1

            result.append({
                **task,
                "scheduled_date": (today + timedelta(days=day_offset + 1)).isoformat(),
                "task_type": task.get("task_type", "study"),
            })

        return result


# ── Singleton ────────────────────────────────────────────────
_planner: Optional[PlannerService] = None


def get_planner_service() -> PlannerService:
    global _planner
    if _planner is None:
        _planner = PlannerService()
    return _planner
