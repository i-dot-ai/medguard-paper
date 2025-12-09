import datetime
import re
from typing import List, Tuple


# Month mappings (case-insensitive)
MONTHS = {
    "january": 1,
    "jan": 1,
    "february": 2,
    "feb": 2,
    "march": 3,
    "mar": 3,
    "april": 4,
    "apr": 4,
    "may": 5,
    "june": 6,
    "jun": 6,
    "july": 7,
    "jul": 7,
    "august": 8,
    "aug": 8,
    "september": 9,
    "sep": 9,
    "sept": 9,
    "october": 10,
    "oct": 10,
    "november": 11,
    "nov": 11,
    "december": 12,
    "dec": 12,
}


def extract_dates(text: str) -> List[Tuple[datetime.date, int, int]]:
    """
    Extract dates from text and return them with their positions.

    Args:
        text: The input text to search for dates

    Returns:
        A list of tuples containing (date, start_index, end_index) where:
        - date is a datetime.date object
        - start_index is the starting position in the text (includes 'on'/'in' if present)
        - end_index is the ending position in the text
    """
    results = []

    # Pattern components
    # Optional preposition (on/in) - captured in group 1
    preposition = r"(?:(on|in)\s+)?"

    # Day with optional ordinal suffix (1-31, with optional st/nd/rd/th)
    day = r"(\d{1,2})(?:st|nd|rd|th)?"

    # Month (full or abbreviated, case-insensitive)
    month_pattern = r"(january|jan|february|feb|march|mar|april|apr|may|june|jun|july|jul|august|aug|september|sept|sep|october|oct|november|nov|december|dec)"

    # Year (4 digits)
    year = r"(\d{4})"

    # Separator (space, hyphen, or special hyphen characters)
    separator = r"[\s\-\u2010-\u2015]+"

    # Pattern 1: [on/in] Day Month Year
    # Examples: "3 June 2021", "on 6th Apr 2021", "06 Apr 2022", "14‑Nov‑2024"
    pattern1 = preposition + day + separator + month_pattern + separator + year

    # Pattern 2: [in] Month Year (no day)
    # Examples: "April 2022", "in Jan 2023", "march 2025"
    pattern2 = preposition + month_pattern + separator + year

    # Pattern 3: [on/in] DD-MM-YYYY format
    # Examples: "23‑06‑2020", "on 15-03-2018"
    # Day (2 digits), Month (2 digits), Year (4 digits)
    day_numeric = r"(\d{2})"
    month_numeric = r"(\d{2})"
    pattern3 = (
        preposition
        + day_numeric
        + r"[\-\u2010-\u2015]"
        + month_numeric
        + r"[\-\u2010-\u2015]"
        + year
    )

    # Pattern 4: [in] Standalone Year (2015 onwards)
    # Examples: "in 2020", "2019"
    # Match years from 2015 to 2099, with optional 'in' preposition
    # Use word boundaries to avoid matching parts of other numbers
    pattern4 = preposition + r"\b(20(?:1[5-9]|[2-9][0-9]))\b"

    # Compile patterns with case-insensitive flag
    regex1 = re.compile(pattern1, re.IGNORECASE)
    regex2 = re.compile(pattern2, re.IGNORECASE)
    regex3 = re.compile(pattern3, re.IGNORECASE)
    regex4 = re.compile(pattern4, re.IGNORECASE)

    # Find all Pattern 1 matches (with day)
    for match in regex1.finditer(text):
        prep = match.group(1)  # 'on' or 'in' or None
        day_str = match.group(2)
        month_str = match.group(3).lower()
        year_str = match.group(4)

        day_num = int(day_str)
        month_num = MONTHS[month_str]
        year_num = int(year_str)

        try:
            date = datetime.date(year_num, month_num, day_num)

            # Determine start index based on whether preposition is present
            if prep:
                start = match.start()  # Include the preposition
            else:
                start = match.start()

            end = match.end()

            results.append((date, start, end))
        except ValueError:
            # Invalid date, skip it
            pass

    # Find all Pattern 2 matches (month-year only, no day)
    # We need to exclude matches that are part of Pattern 1
    pattern1_positions = set()
    for match in regex1.finditer(text):
        # Mark the range of this match as occupied
        for i in range(match.start(), match.end()):
            pattern1_positions.add(i)

    for match in regex2.finditer(text):
        # Check if this match overlaps with any Pattern 1 match
        overlaps = False
        for i in range(match.start(), match.end()):
            if i in pattern1_positions:
                overlaps = True
                break

        if overlaps:
            continue

        prep = match.group(1)  # 'on' or 'in' or None
        month_str = match.group(2).lower()
        year_str = match.group(3)

        month_num = MONTHS[month_str]
        year_num = int(year_str)

        try:
            # Default to first day of month
            date = datetime.date(year_num, month_num, 1)

            # Determine start index based on whether preposition is present
            if prep:
                start = match.start()  # Include the preposition
            else:
                start = match.start()

            end = match.end()

            results.append((date, start, end))
        except ValueError:
            # Invalid date, skip it
            pass

    # Track all occupied positions to avoid overlaps
    all_positions = set()
    for match in regex1.finditer(text):
        for i in range(match.start(), match.end()):
            all_positions.add(i)
    for match in regex2.finditer(text):
        overlaps = False
        for i in range(match.start(), match.end()):
            if i in pattern1_positions:
                overlaps = True
                break
        if not overlaps:
            for i in range(match.start(), match.end()):
                all_positions.add(i)

    # Find all Pattern 3 matches (DD-MM-YYYY)
    for match in regex3.finditer(text):
        # Check if this match overlaps with existing matches
        overlaps = False
        for i in range(match.start(), match.end()):
            if i in all_positions:
                overlaps = True
                break

        if overlaps:
            continue

        prep = match.group(1)  # 'on' or 'in' or None
        day_str = match.group(2)
        month_str = match.group(3)
        year_str = match.group(4)

        day_num = int(day_str)
        month_num = int(month_str)
        year_num = int(year_str)

        # Validate month and day
        if month_num < 1 or month_num > 12:
            continue

        try:
            date = datetime.date(year_num, month_num, day_num)

            # Determine start index based on whether preposition is present
            if prep:
                start = match.start()  # Include the preposition
            else:
                start = match.start()

            end = match.end()

            results.append((date, start, end))

            # Mark positions as occupied
            for i in range(start, end):
                all_positions.add(i)
        except ValueError:
            # Invalid date, skip it
            pass

    # Find all Pattern 4 matches (standalone years 2015+)
    for match in regex4.finditer(text):
        # Check if this match overlaps with existing matches
        overlaps = False
        for i in range(match.start(), match.end()):
            if i in all_positions:
                overlaps = True
                break

        if overlaps:
            continue

        prep = match.group(1)  # 'in' or None
        year_str = match.group(2)

        year_num = int(year_str)

        try:
            # Default to first day of year
            date = datetime.date(year_num, 1, 1)

            # Determine start index based on whether preposition is present
            if prep:
                start = match.start()  # Include the preposition
            else:
                start = match.start()

            end = match.end()

            results.append((date, start, end))

            # Mark positions as occupied
            for i in range(start, end):
                all_positions.add(i)
        except ValueError:
            # Invalid date, skip it
            pass

    # Sort results by position in text
    results.sort(key=lambda x: x[1])

    return results


def format_relative_date(parsed_date: datetime.date, current_date: datetime.date) -> str:
    """
    Format the difference between two dates as a relative time string.

    Args:
        parsed_date: The date that was parsed from the text
        current_date: The current date to compare against

    Returns:
        A string describing the relative time difference, or "recently" if the
        parsed date is in the future relative to current_date
    """
    # If parsed date is in the future, return "recently"
    if parsed_date > current_date:
        return "recently"

    # Calculate the difference
    delta = current_date - parsed_date

    # Calculate years, months, and days
    years = 0
    months = 0
    days = delta.days

    # Calculate years
    while days >= 365:
        # Check if we can subtract a full year
        temp_date = parsed_date.replace(year=parsed_date.year + years + 1)
        if temp_date <= current_date:
            years += 1
            days = (current_date - temp_date).days
        else:
            break

    # Now calculate months from the remaining days
    temp_date = parsed_date.replace(year=parsed_date.year + years)
    while months < 12:
        # Try to add a month
        if temp_date.month == 12:
            next_month_date = temp_date.replace(year=temp_date.year + 1, month=1)
        else:
            # Handle different month lengths
            try:
                next_month_date = temp_date.replace(month=temp_date.month + 1)
            except ValueError:
                # Day doesn't exist in next month (e.g., Jan 31 -> Feb 31)
                # Move to last day of next month
                if temp_date.month == 12:
                    next_month_date = datetime.date(temp_date.year + 1, 1, 31)
                else:
                    next_month = temp_date.month + 1
                    # Find last day of next month
                    if next_month in [4, 6, 9, 11]:
                        next_month_date = datetime.date(temp_date.year, next_month, 30)
                    elif next_month == 2:
                        # February - check for leap year
                        year = temp_date.year
                        if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
                            next_month_date = datetime.date(year, 2, 29)
                        else:
                            next_month_date = datetime.date(year, 2, 28)
                    else:
                        next_month_date = datetime.date(temp_date.year, next_month, 31)

        if next_month_date <= current_date:
            months += 1
            temp_date = next_month_date
        else:
            break

    # Calculate remaining days
    days = (current_date - temp_date).days

    # Format output based on the rules
    if years > 0:
        # More than 12 months: "XX years YY months ago"
        if months == 0:
            if years == 1:
                return "1 year ago"
            else:
                return f"{years} years ago"
        else:
            year_str = "1 year" if years == 1 else f"{years} years"
            month_str = "1 month" if months == 1 else f"{months} months"
            return f"{year_str} {month_str} ago"
    elif months > 0:
        # More than 1 month: "XX months and YY days ago"
        if days == 0:
            if months == 1:
                return "1 month ago"
            else:
                return f"{months} months ago"
        else:
            month_str = "1 month" if months == 1 else f"{months} months"
            day_str = "1 day" if days == 1 else f"{days} days"
            return f"{month_str} and {day_str} ago"
    else:
        # Less than 1 month: "XX days ago"
        if days == 0:
            return "today"
        elif days == 1:
            return "1 day ago"
        else:
            return f"{days} days ago"


def replace_absolute_dates_with_relative(text: str, current_date: datetime.date = None) -> str:
    """
    Replace absolute dates in text with relative date descriptions.

    Args:
        text: The input text containing absolute dates
        current_date: The current date to use for comparison (defaults to today)

    Returns:
        The text with absolute dates replaced by relative descriptions
    """
    if current_date is None:
        current_date = datetime.date.today()

    # Extract all dates from the text
    dates = extract_dates(text)

    # Replace dates in reverse order to maintain correct indices
    result = text
    for parsed_date, start, end in reversed(dates):
        relative_str = format_relative_date(parsed_date, current_date)
        result = result[:start] + relative_str + result[end:]

    return result
