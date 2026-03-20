import pytest
from pathlib import Path
import sys
import os
import tempfile
import shutil


@pytest.fixture
def tmp_repo():
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        
        (repo_path / "src").mkdir()
        (repo_path / "tests").mkdir()
        (repo_path / "docs").mkdir()
        
        (repo_path / "src" / "main.py").write_text("def main():\n    pass\n")
        (repo_path / "tests" / "test_main.py").write_text("def test_main():\n    pass\n")
        
        yield repo_path


@pytest.fixture
def mock_ollama():
    from unittest.mock import MagicMock, patch
    
    mock = MagicMock()
    
    with patch("models.ollama_client.ollama", mock):
        yield mock


@pytest.fixture
def sample_python_file(tmp_path):
    file_path = tmp_path / "sample.py"
    file_path.write_text('''
def hello():
    """Say hello."""
    print("Hello, World!")

def add(a, b):
    return a + b

class Calculator:
    def __init__(self):
        self.value = 0
    
    def add(self, x):
        self.value += x
        return self.value
''')
    return file_path


@pytest.fixture
def sample_diff():
    return """--- a/sample.py
+++ b/sample.py
@@ -1,6 +1,6 @@
 def hello():
-    print("Hello, World!")
+    print("Hello, Bartm0ss!")

 def add(a, b):
     return a + b
"""