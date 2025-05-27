"""
test_main.py - Pytest test suite for Data Science File Converter backend
"""
import os
import tempfile
import shutil
import pytest
from fastapi.testclient import TestClient
from backend.main import app, UPLOAD_DIR, CONVERTED_DIR

client = TestClient(app)

def setup_module(module):
    # Ensure upload/converted dirs are clean before tests
    shutil.rmtree(UPLOAD_DIR, ignore_errors=True)
    shutil.rmtree(CONVERTED_DIR, ignore_errors=True)
    UPLOAD_DIR.mkdir(exist_ok=True)
    CONVERTED_DIR.mkdir(exist_ok=True)

def teardown_module(module):
    # Clean up after tests
    shutil.rmtree(UPLOAD_DIR, ignore_errors=True)
    shutil.rmtree(CONVERTED_DIR, ignore_errors=True)

def test_ping():
    resp = client.get("/ping")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

def test_py_to_ipynb_conversion():
    py_content = """#%%\n# This is a markdown cell\n#%%\nprint('Hello')\n"""
    with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
        f.write(py_content.encode())
        f.flush()
        f.seek(0)
        with open(f.name, 'rb') as file_obj:
            files = {'file': (os.path.basename(f.name), file_obj)}
            data = {'target_format': '.ipynb'}
            resp = client.post("/upload/", files=files, data=data)
        assert resp.status_code == 200
        file_id = resp.json()['file_id']
        # Download
        download = client.get(f"/download/{file_id}")
        assert download.status_code == 200
        content_disp = download.headers.get('content-disposition', '')
        assert content_disp.endswith('.ipynb"') or '.ipynb' in content_disp
        assert download.headers['content-type'] in ['application/json', 'application/octet-stream', 'application/x-ipynb+json']
    os.unlink(f.name)

def test_csv_to_json_conversion():
    csv_content = "col1,col2\n1,2\n3,4\n"
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
        f.write(csv_content.encode())
        f.flush()
        f.seek(0)
        with open(f.name, 'rb') as file_obj:
            files = {'file': (os.path.basename(f.name), file_obj)}
            data = {'target_format': '.json'}
            resp = client.post("/upload/", files=files, data=data)
        assert resp.status_code == 200
        file_id = resp.json()['file_id']
        # Download
        download = client.get(f"/download/{file_id}")
        assert download.status_code == 200
        content_disp = download.headers.get('content-disposition', '')
        assert content_disp.endswith('.json"') or '.json' in content_disp
        assert 'application/json' in download.headers['content-type'] or 'application/octet-stream' in download.headers['content-type']
    os.unlink(f.name)

def test_invalid_conversion():
    txt_content = "hello world"
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
        f.write(txt_content.encode())
        f.flush()
        f.seek(0)
        with open(f.name, 'rb') as file_obj:
            files = {'file': (os.path.basename(f.name), file_obj)}
            data = {'target_format': '.ipynb'}
            resp = client.post("/upload/", files=files, data=data)
        assert resp.status_code == 400
    os.unlink(f.name)
