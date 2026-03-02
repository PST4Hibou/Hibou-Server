

from pathlib import Path
from helpers.json import write_json, read_json 

class TestJson:
    def test_write_read_json(self, tmp_path: Path):
        data = {"name": "Alice", "age": 30, "scores": [95, 87, 92]}
        file_path = tmp_path / "test.json"
        
        write_json(file_path, data)
        
        assert file_path.exists()
        assert file_path.is_file()
        read_data = read_json(file_path)
        assert read_data == data
        

