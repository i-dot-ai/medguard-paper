import datetime
from medguard.vignette.parser.parser import (
    format_relative_date,
    replace_absolute_dates_with_relative,
)


def test_format_relative_date_future():
    """Test that future dates return 'recently'"""
    current_date = datetime.date(2024, 10, 29)

    # Future dates should return "recently"
    future_date = datetime.date(2025, 1, 15)
    result = format_relative_date(future_date, current_date)
    assert result == "recently"

    future_date = datetime.date(2024, 11, 5)
    result = format_relative_date(future_date, current_date)
    assert result == "recently"


def test_format_relative_date_same_day():
    """Test that same day returns 'today'"""
    current_date = datetime.date(2024, 10, 29)
    parsed_date = datetime.date(2024, 10, 29)

    result = format_relative_date(parsed_date, current_date)
    assert result == "today"


def test_format_relative_date_days_ago():
    """Test dates less than 1 month ago"""
    current_date = datetime.date(2024, 10, 29)

    # 1 day ago
    parsed_date = datetime.date(2024, 10, 28)
    result = format_relative_date(parsed_date, current_date)
    assert result == "1 day ago"

    # 4 days ago
    parsed_date = datetime.date(2024, 10, 25)
    result = format_relative_date(parsed_date, current_date)
    assert result == "4 days ago"

    # 14 days ago
    parsed_date = datetime.date(2024, 10, 15)
    result = format_relative_date(parsed_date, current_date)
    assert result == "14 days ago"

    # 28 days ago
    parsed_date = datetime.date(2024, 10, 1)
    result = format_relative_date(parsed_date, current_date)
    assert result == "28 days ago"


def test_format_relative_date_months_ago():
    """Test dates between 1-12 months ago"""
    current_date = datetime.date(2024, 10, 29)

    # Exactly 1 month ago
    parsed_date = datetime.date(2024, 9, 29)
    result = format_relative_date(parsed_date, current_date)
    assert result == "1 month ago"

    # 1 month and 14 days ago
    parsed_date = datetime.date(2024, 9, 15)
    result = format_relative_date(parsed_date, current_date)
    assert result == "1 month and 14 days ago"

    # 2 months ago
    parsed_date = datetime.date(2024, 8, 29)
    result = format_relative_date(parsed_date, current_date)
    assert result == "2 months ago"

    # 2 months and 14 days ago
    parsed_date = datetime.date(2024, 8, 15)
    result = format_relative_date(parsed_date, current_date)
    assert result == "2 months and 14 days ago"

    # 7 months and 14 days ago
    parsed_date = datetime.date(2024, 3, 15)
    result = format_relative_date(parsed_date, current_date)
    assert result == "7 months and 14 days ago"

    # 10 months ago
    parsed_date = datetime.date(2023, 12, 29)
    result = format_relative_date(parsed_date, current_date)
    assert result == "10 months ago"


def test_format_relative_date_years_ago():
    """Test dates more than 12 months ago"""
    current_date = datetime.date(2024, 10, 29)

    # Exactly 1 year ago
    parsed_date = datetime.date(2023, 10, 29)
    result = format_relative_date(parsed_date, current_date)
    assert result == "1 year ago"

    # 1 year 4 months ago
    parsed_date = datetime.date(2023, 6, 15)
    result = format_relative_date(parsed_date, current_date)
    assert result == "1 year 4 months ago"

    # 2 years ago
    parsed_date = datetime.date(2022, 10, 29)
    result = format_relative_date(parsed_date, current_date)
    assert result == "2 years ago"

    # 2 years 4 months ago
    parsed_date = datetime.date(2022, 6, 15)
    result = format_relative_date(parsed_date, current_date)
    assert result == "2 years 4 months ago"

    # 3 years 7 months ago
    parsed_date = datetime.date(2021, 3, 15)
    result = format_relative_date(parsed_date, current_date)
    assert result == "3 years 7 months ago"


def test_replace_single_date():
    """Test replacing a single date in text"""
    current_date = datetime.date(2024, 10, 29)

    text = "The meeting was on 3 June 2021."
    result = replace_absolute_dates_with_relative(text, current_date)
    assert result == "The meeting was 3 years 4 months ago."

    text = "Report due 12 May 2023 end of day."
    result = replace_absolute_dates_with_relative(text, current_date)
    assert result == "Report due 1 year 5 months ago end of day."


def test_replace_future_date():
    """Test replacing future dates with 'recently'"""
    current_date = datetime.date(2024, 10, 29)

    text = "Last updated: 14‑Nov‑2024"
    result = replace_absolute_dates_with_relative(text, current_date)
    assert result == "Last updated: recently"

    text = "The event in march 2025 was great."
    result = replace_absolute_dates_with_relative(text, current_date)
    assert result == "The event recently was great."


def test_replace_multiple_dates():
    """Test replacing multiple dates in the same text"""
    current_date = datetime.date(2024, 10, 29)

    text = "Events on 4 Jan 2024 and 19 Dec 2024 are confirmed."
    result = replace_absolute_dates_with_relative(text, current_date)
    assert result == "Events 9 months and 25 days ago and recently are confirmed."

    text = "Our journey began in January 2023 when we first met. We got engaged on 14‑Nov‑2024."
    result = replace_absolute_dates_with_relative(text, current_date)
    assert (
        result
        == "Our journey began 1 year 9 months ago when we first met. We got engaged recently."
    )


def test_replace_with_month_year_format():
    """Test replacing dates that only have month and year"""
    current_date = datetime.date(2024, 10, 29)

    text = "Published in April 2022 edition."
    result = replace_absolute_dates_with_relative(text, current_date)
    assert result == "Published 2 years 6 months ago edition."

    text = "Data from Jan 2023 shows improvement."
    result = replace_absolute_dates_with_relative(text, current_date)
    assert result == "Data from 1 year 9 months ago shows improvement."


def test_replace_preserves_non_date_text():
    """Test that non-date text is preserved exactly"""
    current_date = datetime.date(2024, 10, 29)

    text = "Before on 3 June 2021 after."
    result = replace_absolute_dates_with_relative(text, current_date)
    assert result == "Before 3 years 4 months ago after."
    assert result.startswith("Before ")
    assert result.endswith(" after.")


def test_replace_with_various_formats():
    """Test replacing dates in various formats"""
    current_date = datetime.date(2024, 10, 29)

    # Lowercase month (defaults to 1st of month: March 1, 2024)
    text = "Event in mar 2024 was successful."
    result = replace_absolute_dates_with_relative(text, current_date)
    assert result == "Event 7 months and 28 days ago was successful."

    # Ordinal suffix
    text = "Meeting on 6th Apr 2024 confirmed."
    result = replace_absolute_dates_with_relative(text, current_date)
    assert result == "Meeting 6 months and 23 days ago confirmed."

    # Two-digit day
    text = "Updated on 06 Apr 2022 by system."
    result = replace_absolute_dates_with_relative(text, current_date)
    assert result == "Updated 2 years 6 months ago by system."


def test_replace_empty_and_no_dates():
    """Test with empty strings and strings without dates"""
    current_date = datetime.date(2024, 10, 29)

    # Empty string
    text = ""
    result = replace_absolute_dates_with_relative(text, current_date)
    assert result == ""

    # No dates
    text = "This text has no dates in it at all."
    result = replace_absolute_dates_with_relative(text, current_date)
    assert result == "This text has no dates in it at all."


def test_replace_three_dates():
    """Test replacing three dates in one string"""
    current_date = datetime.date(2024, 10, 29)

    text = "The events on 3 June 2021, 12 May 2023, and in December 2024 were all successful."
    result = replace_absolute_dates_with_relative(text, current_date)
    # Verify it has three replacements
    assert "3 years 4 months ago" in result
    assert "1 year 5 months ago" in result
    assert "recently" in result
    # Check structure is preserved
    assert result.startswith("The events ")
    assert " were all successful." in result


def test_replace_four_dates():
    """Test replacing four dates in one string"""
    current_date = datetime.date(2024, 10, 29)

    text = "Quarterly reports: on 15th Jan 2024, 06 Apr 2022, in Nov 2022, and 19 Dec 2024."
    result = replace_absolute_dates_with_relative(text, current_date)
    # Verify it has four replacements
    assert "9 months and 14 days ago" in result
    assert "2 years 6 months ago" in result
    assert "1 year 11 months ago" in result
    assert "recently" in result


def test_replace_dd_mm_yyyy_format():
    """Test replacing DD-MM-YYYY format dates"""
    current_date = datetime.date(2024, 10, 29)

    # Single DD-MM-YYYY date
    text = "Event date: 23‑06‑2020"
    result = replace_absolute_dates_with_relative(text, current_date)
    assert result == "Event date: 4 years 4 months ago"

    # With preposition
    text = "Born on 15-03-2018 in London."
    result = replace_absolute_dates_with_relative(text, current_date)
    assert result == "Born 6 years 7 months ago in London."

    # Multiple DD-MM-YYYY dates
    text = "Dates: 01-01-2020 and 31-12-2021"
    result = replace_absolute_dates_with_relative(text, current_date)
    assert "4 years 9 months ago" in result
    assert "2 years 10 months ago" in result


def test_replace_standalone_years():
    """Test replacing standalone year formats"""
    current_date = datetime.date(2024, 10, 29)

    # Single year with preposition
    text = "The project started in 2020."
    result = replace_absolute_dates_with_relative(text, current_date)
    assert result == "The project started 4 years 9 months ago."

    # Multiple years
    text = "From 2016 to 2023 we grew significantly."
    result = replace_absolute_dates_with_relative(text, current_date)
    assert "8 years 9 months ago" in result
    assert "1 year 9 months ago" in result

    # Year at start
    text = "2019 was a great year."
    result = replace_absolute_dates_with_relative(text, current_date)
    assert result == "5 years 9 months ago was a great year."

    # Should not match years before 2015
    text = "Born in 2010 and 2014."
    result = replace_absolute_dates_with_relative(text, current_date)
    assert result == "Born in 2010 and 2014."


if __name__ == "__main__":
    # Run all tests
    test_format_relative_date_future()
    test_format_relative_date_same_day()
    test_format_relative_date_days_ago()
    test_format_relative_date_months_ago()
    test_format_relative_date_years_ago()
    test_replace_single_date()
    test_replace_future_date()
    test_replace_multiple_dates()
    test_replace_with_month_year_format()
    test_replace_preserves_non_date_text()
    test_replace_with_various_formats()
    test_replace_empty_and_no_dates()
    test_replace_three_dates()
    test_replace_four_dates()
    test_replace_dd_mm_yyyy_format()
    test_replace_standalone_years()
    print("All relative date tests passed!")
