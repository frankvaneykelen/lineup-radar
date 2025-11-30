"""
Tests for CSV loading and saving operations.
"""
import pytest
import csv
from pathlib import Path
from fetch_festival_data import load_csv, save_csv


class TestCSVOperations:
    """Tests for CSV file operations."""
    
    def test_load_csv(self, temp_csv_file, sample_csv_data):
        """Test CSV loading."""
        headers, rows = load_csv(temp_csv_file)
        
        assert headers == sample_csv_data['headers']
        assert len(rows) == 1
        assert rows[0]['Artist'] == 'Test Artist'
        assert rows[0]['Genre'] == 'Rock'
    
    def test_save_csv(self, tmp_path, sample_csv_data):
        """Test CSV saving."""
        csv_file = tmp_path / "output.csv"
        
        save_csv(csv_file, sample_csv_data['headers'], sample_csv_data['rows'])
        
        # Verify file exists and can be read
        assert csv_file.exists()
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert len(rows) == 1
            assert rows[0]['Artist'] == 'Test Artist'
    
    def test_load_nonexistent_csv(self, tmp_path):
        """Test loading non-existent CSV."""
        csv_file = tmp_path / "nonexistent.csv"
        
        with pytest.raises(SystemExit):
            load_csv(csv_file)
    
    def test_save_and_reload_csv(self, tmp_path, sample_csv_data):
        """Test saving and reloading preserves data."""
        csv_file = tmp_path / "test.csv"
        
        # Save
        save_csv(csv_file, sample_csv_data['headers'], sample_csv_data['rows'])
        
        # Reload
        headers, rows = load_csv(csv_file)
        
        assert headers == sample_csv_data['headers']
        assert len(rows) == len(sample_csv_data['rows'])
        assert rows[0] == sample_csv_data['rows'][0]
    
    def test_csv_utf8_encoding(self, tmp_path):
        """Test CSV handles UTF-8 characters correctly."""
        csv_file = tmp_path / "utf8_test.csv"
        headers = ['Artist', 'Bio']
        rows = [
            {'Artist': 'Ärtiśt Nãmé', 'Bio': 'Testbio met €uro en 日本語'},
        ]
        
        save_csv(csv_file, headers, rows)
        loaded_headers, loaded_rows = load_csv(csv_file)
        
        assert loaded_rows[0]['Artist'] == 'Ärtiśt Nãmé'
        assert '€uro' in loaded_rows[0]['Bio']
        assert '日本語' in loaded_rows[0]['Bio']
