from datetime import date, datetime, timedelta

from medguard.data_ingest.mappings import frailty_deficit_lookup, qof_register_lookup


def get_random_date_between(start: datetime, end: datetime) -> datetime:
    from random import randint

    return start + timedelta(days=randint(0, (end - start).days - 1))


def get_first_non_null(*attributes):
    """Helper function to get the first non-null attribute from an object"""

    def getter(self):
        for attr in attributes:
            value = getattr(self, attr, None)
            if value is not None:
                return value
        return None

    return getter


def format_datetime(dt: datetime, include_time: bool = False) -> str:
    if include_time:
        return dt.strftime("%A %d %B %Y %H.%M%p")
    else:
        return dt.strftime("%A %d %B %Y")


def datetime_midpoint(start: datetime, end: datetime) -> datetime:
    """Calculate the midpoint between two datetime objects."""
    return start + (end - start) / 2


def format_date(d: date | None) -> str:
    """Format a date as a human-friendly string; returns "Unknown date" if None."""
    if not d:
        return "Unknown date"
    return d.strftime("%A %d %B %Y")


def update_prompt(res: str, field: str | None, descriptor: str = "", newline=True):
    if field:
        newline_token = "\n" if newline else ""
        res += newline_token + descriptor + field
    return res


def update_datetime_prompt(
    res: str,
    dt: datetime | None,
    descriptor: str = "",
    include_time: bool = False,
    newline: bool = True,
) -> str:
    """Append a formatted datetime to the prompt only if non-null.

    - descriptor: prefix to include before the formatted datetime (e.g., "Discharge date: ")
    - include_time: whether to include time in the formatting
    - newline: whether to prepend a newline before appending
    """
    if dt is None:
        return res
    newline_token = "\n" if newline else ""
    return res + newline_token + descriptor + format_datetime(dt, include_time)


def format_qof_registers(qof_registers: str) -> str:
    return "\n".join([f"- {qof_register_lookup.get(r, r)}" for r in qof_registers.split("|")])


def qof_registers_to_list(qof_registers: str) -> list[str]:
    if qof_registers is None:
        return []
    return [qof_register_lookup.get(r, r) for r in qof_registers.split("|")]


def frailty_deficit_list_to_list(frailty_deficit_list: str) -> list[str]:
    if frailty_deficit_list is None:
        return []
    return [frailty_deficit_lookup.get(r, r) for r in frailty_deficit_list.split("|")]


def format_frailty_deficit_list(frailty_deficit_list: str) -> str:
    return "\n".join(
        [f"- {frailty_deficit_lookup.get(r, r)}" for r in frailty_deficit_list.split("|")]
    )


def calculate_age(date_of_birth: date, reference_date: date) -> int | None:
    """
    Calculate age in years from date of birth to a reference date.

    Args:
        date_of_birth: The person's date of birth
        reference_date: The date to calculate age at

    Returns:
        Age in years, or None if calculation fails

    Example:
        >>> calculate_age(date(2000, 3, 15), date(2024, 2, 10))
        23  # Birthday hasn't happened yet
        >>> calculate_age(date(2000, 3, 15), date(2024, 4, 1))
        24  # Birthday has passed
    """
    try:
        age = (
            reference_date.year
            - date_of_birth.year
            - (
                (reference_date.month, reference_date.day)
                < (date_of_birth.month, date_of_birth.day)
            )
        )
        return age
    except Exception:
        return None
