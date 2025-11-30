# Unit Tests

This directory contains unit tests for the festival lineup tracker.

## Structure

- `conftest.py` - Pytest configuration and shared fixtures
- `test_config.py` - Tests for festival configuration
- `test_csv_operations.py` - Tests for CSV loading/saving
- `test_fetch_festival_data.py` - Tests for festival data fetching
- `test_scraper.py` - Tests for web scraping functionality
- `test_slug.py` - Tests for artist name slugification

## Running Tests

### Run all tests
```powershell
pytest tests/ -v
```

### Run specific test file
```powershell
pytest tests/test_config.py -v
```

### Run specific test
```powershell
pytest tests/test_config.py::TestGetFestivalConfig::test_get_dtrh_config -v
```

### Run with coverage
```powershell
pytest tests/ --cov=. --cov-report=html
```

## Test Coverage

Current test coverage:
- ✅ `festival_helpers/config.py` - Configuration loading
- ✅ `festival_helpers/slug.py` - Artist name slugification
- ✅ `festival_helpers/scraper.py` - Web scraping (partial)
- ✅ `fetch_festival_data.py` - Festival data fetching (partial)
- ✅ CSV operations - Load/save functionality

## Fixtures

Available test fixtures (defined in `conftest.py`):
- `sample_dtrh_config` - DTRH festival configuration
- `sample_pinkpop_config` - Pinkpop festival configuration  
- `sample_artist_html_dtrh` - Sample DTRH artist page HTML
- `sample_artist_html_pinkpop` - Sample Pinkpop artist page HTML
- `sample_lineup_html` - Sample lineup page HTML
- `sample_csv_data` - Sample CSV data structure
- `temp_csv_file` - Temporary CSV file for testing

## Notes

- Tests use mocking to avoid making real HTTP requests
- Temporary files are created in `pytest`'s tmp_path
- Some tests currently fail due to implementation differences - these will be fixed as the codebase evolves
- Run tests before committing changes to ensure nothing breaks

## Test Results Summary

**Status**: 30/54 tests passing (55.6%)

**Passing Tests**:
- All configuration tests (festival loading)
- All CSV operation tests
- All basic slug tests
- Festival data needs checking tests

**Known Issues**:
- FestivalConfig requires `year` parameter (fixtures need updating)
- get_sort_name doesn't rearrange articles (implementation difference)
- extract_social_links function differs from expected API

These test failures represent opportunities for improvement and will be addressed in future updates.
