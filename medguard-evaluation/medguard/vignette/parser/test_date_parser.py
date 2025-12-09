import datetime

from medguard.vignette.parser.parser import extract_dates


def test_day_month_year_formats():
    """Test standard day-month-year formats"""
    # Test with full month name
    text = "The meeting is on 3 June 2021 at noon."
    results = extract_dates(text)
    assert len(results) == 1
    date, start, end = results[0]
    assert date == datetime.date(2021, 6, 3)
    assert text[start:end] == "on 3 June 2021"

    # Test with abbreviated month
    text = "Report due 12 May 2023 end of day."
    results = extract_dates(text)
    assert len(results) == 1
    date, start, end = results[0]
    assert date == datetime.date(2023, 5, 12)
    assert text[start:end] == "12 May 2023"

    # Test with short month
    text = "Deadline: 6 Dec 2024"
    results = extract_dates(text)
    assert len(results) == 1
    date, start, end = results[0]
    assert date == datetime.date(2024, 12, 6)
    assert text[start:end] == "6 Dec 2024"


def test_two_digit_day_formats():
    """Test dates with two-digit day numbers"""
    text = "Updated on 06 Apr 2022 by system."
    results = extract_dates(text)
    assert len(results) == 1
    date, start, end = results[0]
    assert date == datetime.date(2022, 4, 6)
    assert text[start:end] == "on 06 Apr 2022"


def test_month_year_only_formats():
    """Test month-year formats (no day specified)"""
    # Full month name
    text = "Published at April 2022 edition."
    results = extract_dates(text)
    assert len(results) == 1
    date, start, end = results[0]
    assert date == datetime.date(2022, 4, 1)  # Should default to first day
    assert text[start:end] == "April 2022"

    # Full month name (longer)
    text = "Starting November 2022 onwards."
    results = extract_dates(text)
    assert len(results) == 1
    date, start, end = results[0]
    assert date == datetime.date(2022, 11, 1)
    assert text[start:end] == "November 2022"

    # Abbreviated month
    text = "Data from Jan 2023 shows improvement."
    results = extract_dates(text)
    assert len(results) == 1
    date, start, end = results[0]
    assert date == datetime.date(2023, 1, 1)
    assert text[start:end] == "Jan 2023"


def test_lowercase_formats():
    """Test lowercase month names"""
    text = "The event in mar 2024 was great."
    results = extract_dates(text)
    assert len(results) == 1
    date, start, end = results[0]
    assert date == datetime.date(2024, 3, 1)
    assert text[start:end] == "in mar 2024"

    text = "Expected march 2025 release."
    results = extract_dates(text)
    assert len(results) == 1
    date, start, end = results[0]
    assert date == datetime.date(2025, 3, 1)
    assert text[start:end] == "march 2025"


def test_special_hyphen_format():
    """Test dates with special hyphen characters"""
    text = "Last updated: 14‑Nov‑2024"
    results = extract_dates(text)
    assert len(results) == 1
    date, start, end = results[0]
    assert date == datetime.date(2024, 11, 14)
    assert text[start:end] == "14‑Nov‑2024"


def test_with_preposition_on():
    """Test dates preceded by 'on' - should include 'on' in start index"""
    # With ordinal day
    text = "It happened on 6th Apr 2021 afternoon."
    results = extract_dates(text)
    assert len(results) == 1
    date, start, end = results[0]
    assert date == datetime.date(2021, 4, 6)
    assert text[start:end] == "on 6th Apr 2021"

    # Without ordinal
    text = "Meeting on 8 may 2021 confirmed."
    results = extract_dates(text)
    assert len(results) == 1
    date, start, end = results[0]
    assert date == datetime.date(2021, 5, 8)
    assert text[start:end] == "on 8 may 2021"


def test_with_preposition_in():
    """Test dates preceded by 'in' - should include 'in' in start index"""
    text = "Published in Jan 2023 quarterly report."
    results = extract_dates(text)
    assert len(results) == 1
    date, start, end = results[0]
    assert date == datetime.date(2023, 1, 1)
    assert text[start:end] == "in Jan 2023"


def test_multiple_dates_in_text():
    """Test extracting multiple dates from same text"""
    text = "Events on 4 Jan 2024 and 19 Dec 2024 are confirmed."
    results = extract_dates(text)
    assert len(results) == 2

    date1, start1, end1 = results[0]
    assert date1 == datetime.date(2024, 1, 4)
    assert text[start1:end1] == "on 4 Jan 2024"

    date2, start2, end2 = results[1]
    assert date2 == datetime.date(2024, 12, 19)
    assert text[start2:end2] == "19 Dec 2024"


def test_mixed_case_months():
    """Test dates with mixed case month names"""
    text = "Released in January 2023 version."
    results = extract_dates(text)
    assert len(results) == 1
    date, start, end = results[0]
    assert date == datetime.date(2023, 1, 1)
    assert text[start:end] == "in January 2023"


def test_ordinal_suffixes():
    """Test dates with ordinal suffixes (1st, 2nd, 3rd, 4th, etc)"""
    text = "Event on 21st Dec 2024 at venue."
    results = extract_dates(text)
    assert len(results) == 1
    date, start, end = results[0]
    assert date == datetime.date(2024, 12, 21)
    assert text[start:end] == "on 21st Dec 2024"

    text = "Meeting on 2nd Mar 2024 morning."
    results = extract_dates(text)
    assert len(results) == 1
    date, start, end = results[0]
    assert date == datetime.date(2024, 3, 2)
    assert text[start:end] == "on 2nd Mar 2024"

    text = "Deadline on 23rd Apr 2024."
    results = extract_dates(text)
    assert len(results) == 1
    date, start, end = results[0]
    assert date == datetime.date(2024, 4, 23)
    assert text[start:end] == "on 23rd Apr 2024"


def test_no_dates_in_text():
    """Test text with no dates"""
    text = "This is just some random text with no dates."
    results = extract_dates(text)
    assert len(results) == 0


def test_complex_text_with_multiple_formats():
    """Test complex text with various date formats"""
    text = """
    The project started in April 2022 and the first milestone
    was reached on 6th Apr 2021. We had updates on 14‑Nov‑2024
    and plan to finish in march 2025.
    """
    results = extract_dates(text)
    assert len(results) == 4

    # Check each date is correctly parsed
    dates = [result[0] for result in results]
    assert datetime.date(2022, 4, 1) in dates
    assert datetime.date(2021, 4, 6) in dates
    assert datetime.date(2024, 11, 14) in dates
    assert datetime.date(2025, 3, 1) in dates


def test_three_dates_in_single_string():
    """Test extracting three dates from a single string"""
    text = "The events on 3 June 2021, 12 May 2023, and in December 2024 were all successful."
    results = extract_dates(text)
    assert len(results) == 3

    date1, start1, end1 = results[0]
    assert date1 == datetime.date(2021, 6, 3)
    assert text[start1:end1] == "on 3 June 2021"

    date2, start2, end2 = results[1]
    assert date2 == datetime.date(2023, 5, 12)
    assert text[start2:end2] == "12 May 2023"

    date3, start3, end3 = results[2]
    assert date3 == datetime.date(2024, 12, 1)
    assert text[start3:end3] == "in December 2024"


def test_four_dates_mixed_formats():
    """Test extracting four dates with mixed formats"""
    text = "Quarterly reports: on 15th Jan 2024, 06 Apr 2022, in Nov 2022, and 19 Dec 2024."
    results = extract_dates(text)
    assert len(results) == 4

    date1, start1, end1 = results[0]
    assert date1 == datetime.date(2024, 1, 15)
    assert text[start1:end1] == "on 15th Jan 2024"

    date2, start2, end2 = results[1]
    assert date2 == datetime.date(2022, 4, 6)
    assert text[start2:end2] == "06 Apr 2022"

    date3, start3, end3 = results[2]
    assert date3 == datetime.date(2022, 11, 1)
    assert text[start3:end3] == "in Nov 2022"

    date4, start4, end4 = results[3]
    assert date4 == datetime.date(2024, 12, 19)
    assert text[start4:end4] == "19 Dec 2024"


def test_four_dates_narrative_text():
    """Test extracting four dates from narrative text"""
    text = """Our journey began in January 2023 when we first met.
    We got engaged on 14‑Nov‑2024, started planning in march 2025,
    and the wedding is scheduled for 8 may 2021."""
    results = extract_dates(text)
    assert len(results) == 4

    dates = [result[0] for result in results]
    assert datetime.date(2023, 1, 1) in dates
    assert datetime.date(2024, 11, 14) in dates
    assert datetime.date(2025, 3, 1) in dates
    assert datetime.date(2021, 5, 8) in dates


def test_dd_mm_yyyy_format():
    """Test DD-MM-YYYY format dates"""
    # Standard format
    text = "Event date: 23‑06‑2020"
    results = extract_dates(text)
    assert len(results) == 1
    date, start, end = results[0]
    assert date == datetime.date(2020, 6, 23)
    assert text[start:end] == "23‑06‑2020"

    # With regular hyphens
    text = "Born on 15-03-2018 in London."
    results = extract_dates(text)
    assert len(results) == 1
    date, start, end = results[0]
    assert date == datetime.date(2018, 3, 15)
    assert text[start:end] == "on 15-03-2018"

    # Multiple DD-MM-YYYY dates
    text = "Dates: 01-01-2020 and 31-12-2021"
    results = extract_dates(text)
    assert len(results) == 2

    date1, start1, end1 = results[0]
    assert date1 == datetime.date(2020, 1, 1)
    assert text[start1:end1] == "01-01-2020"

    date2, start2, end2 = results[1]
    assert date2 == datetime.date(2021, 12, 31)
    assert text[start2:end2] == "31-12-2021"


def test_standalone_years():
    """Test standalone year formats (2015 onwards)"""
    # Single year
    text = "The project started in 2020."
    results = extract_dates(text)
    assert len(results) == 1
    date, start, end = results[0]
    assert date == datetime.date(2020, 1, 1)
    assert text[start:end] == "in 2020"

    # Year without preposition
    text = "Back in 2015 things were different."
    results = extract_dates(text)
    assert len(results) == 1
    date, start, end = results[0]
    assert date == datetime.date(2015, 1, 1)
    assert text[start:end] == "in 2015"

    # Multiple years
    text = "From 2016 to 2023 we grew significantly."
    results = extract_dates(text)
    assert len(results) == 2

    date1, start1, end1 = results[0]
    assert date1 == datetime.date(2016, 1, 1)

    date2, start2, end2 = results[1]
    assert date2 == datetime.date(2023, 1, 1)

    # Year at start
    text = "2019 was a great year."
    results = extract_dates(text)
    assert len(results) == 1
    date, start, end = results[0]
    assert date == datetime.date(2019, 1, 1)
    assert text[start:end] == "2019"
    assert start == 0

    # Should not match years before 2015
    text = "Born in 2010 and 2014."
    results = extract_dates(text)
    assert len(results) == 0


def test_dates_at_text_boundaries():
    """Test dates at start and end of text"""
    # Date at start
    text = "3 June 2021 was the start date."
    results = extract_dates(text)
    assert len(results) == 1
    date, start, end = results[0]
    assert start == 0
    assert date == datetime.date(2021, 6, 3)

    # Date at end
    text = "Completion date: 12 May 2023"
    results = extract_dates(text)
    assert len(results) == 1
    date, start, end = results[0]
    assert end == len(text)
    assert date == datetime.date(2023, 5, 12)


if __name__ == "__main__":
    # Run all tests
    test_day_month_year_formats()
    test_two_digit_day_formats()
    test_month_year_only_formats()
    test_lowercase_formats()
    test_special_hyphen_format()
    test_with_preposition_on()
    test_with_preposition_in()
    test_multiple_dates_in_text()
    test_mixed_case_months()
    test_ordinal_suffixes()
    test_no_dates_in_text()
    test_complex_text_with_multiple_formats()
    test_three_dates_in_single_string()
    test_four_dates_mixed_formats()
    test_four_dates_narrative_text()
    test_dd_mm_yyyy_format()
    test_standalone_years()
    test_dates_at_text_boundaries()
    print("All tests passed!")
