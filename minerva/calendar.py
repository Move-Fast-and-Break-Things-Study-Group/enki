from datetime import datetime, timedelta
from typing import List, NamedTuple, Optional
import icalendar
import recurring_ical_events


class Event(NamedTuple):
  summary: str
  description: str
  meet_url: Optional[str]
  start: datetime
  end: datetime
  recurrence_rule: Optional[icalendar.vRecur]


def parse_ics(ics_content: str) -> List[Event]:
  cal = icalendar.Calendar.from_ical(ics_content)
  events = []
  for component in cal.walk():
    if component.name == "VEVENT":
      summary = str(component.get("summary"))
      description = _trim_google_meet_links_from_description(str(component.get("description", "")))
      x_google_conference = str(component.get("x-google-conference"))
      start = component.get("dtstart").dt
      end = component.get("dtend").dt
      rrule = component.get("rrule")
      events.append(Event(summary, description, x_google_conference, start, end, rrule))
  return events


def _trim_google_meet_links_from_description(description: str) -> str:
  """Remove Google Meet links and help from the event description

  Google Calendar adds text with the Google Meet link and Google Meet help to the
  end of the event description. This function removes that text to make the
  description less noisy. We extract the Google Meet event link from the
  x-google-conference property.
  """

  # Remove the last three lines from the description if the third to last contains "Google Meet: https://"
  lines = description.splitlines()
  if len(lines) >= 3 and "Google Meet: https://" in lines[-3]:
    return "\n".join(lines[:-3]).strip()


def parse_ics_v2(ics_content: str) -> List[Event]:
  cal = icalendar.Calendar.from_ical(ics_content)
  filtered_cal = recurring_ical_events.of(cal).between(datetime.now() + timedelta(days=40), timedelta(days=28))
  events = []
  for component in filtered_cal:
    if component.name == "VEVENT":
      summary = str(component.get("summary"))
      description = _trim_google_meet_links_from_description(str(component.get("description", "")))
      x_google_conference = str(component.get("x-google-conference"))
      start = component.get("dtstart").dt
      end = component.get("dtend").dt
      rrule = component.get("rrule")
      events.append(Event(summary, description, x_google_conference, start, end, rrule))
  return events


def is_event_in_next_2_weeks(event: Event) -> bool:
  """Check if the event is in the next 2 weeks

  The event is considered to be in the next 2 weeks if the start date is within
  the next 14 days.
  """

  now = datetime.now(event.start.tzinfo)
  return now <= event.start <= now + timedelta(days=14)
