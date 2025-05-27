# main.py - Backend for Data Science File Converter
# FastAPI app for converting between data science file formats

from fastapi import FastAPI, UploadFile, File, HTTPException  # FastAPI imports for API and file handling
from fastapi.responses import FileResponse, JSONResponse      # For file and JSON responses
from fastapi.middleware.cors import CORSMiddleware           # For CORS support
import os
import shutil
import uuid
from pathlib import Path
import nbformat                                               # For .ipynb file creation
import pandas as pd                                          # For tabular data conversions
import json

app = FastAPI()

# Enable CORS for all origins (for frontend dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],  # <-- Expose Content-Disposition for frontend
)

# Directories for uploads and converted files (always inside backend/)
BACKEND_DIR = Path(__file__).parent.resolve()
UPLOAD_DIR = BACKEND_DIR / "uploads"
CONVERTED_DIR = BACKEND_DIR / "converted"
UPLOAD_DIR.mkdir(exist_ok=True)
CONVERTED_DIR.mkdir(exist_ok=True)

# Supported file conversions (input_ext, output_ext)
SUPPORTED_CONVERSIONS = {
    ('.py', '.ipynb'),
    ('.csv', '.json'),
    ('.json', '.csv'),
    ('.xlsx', '.csv'),
    ('.csv', '.xlsx'),
    ('.csv', '.parquet'),
    ('.parquet', '.csv'),
    ('.csv', '.hdf5'),
    ('.hdf5', '.csv'),
}

def py_to_ipynb(py_path, ipynb_path):
    """
    Convert a Spyder .py file to a Jupyter .ipynb file.
    - #%% or # %% marks code cells
    - Comments before code cells become markdown cells
    """
    with open(py_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    nb = nbformat.v4.new_notebook()  # Create a new notebook object
    cells = []
    cell_lines = []
    markdown_lines = []
    in_code = False

    def flush_cell():
        # Helper to flush accumulated lines into notebook cells
        nonlocal cell_lines, markdown_lines
        if markdown_lines:
            cells.append(nbformat.v4.new_markdown_cell(''.join(markdown_lines).strip()))
            markdown_lines = []
        if cell_lines:
            cells.append(nbformat.v4.new_code_cell(''.join(cell_lines).strip()))
            cell_lines = []

    for line in lines:
        if line.strip().startswith('#%%'):
            flush_cell()  # New code cell marker
            in_code = True
        elif line.strip().startswith('#') and not in_code:
            markdown_lines.append(line.lstrip('#').lstrip())  # Markdown before code
        else:
            in_code = True
            cell_lines.append(line)  # Code lines
    flush_cell()  # Flush any remaining lines
    nb['cells'] = cells
    with open(ipynb_path, 'w', encoding='utf-8') as f:
        nbformat.write(nb, f)

def convert_file(input_path, output_path, input_ext, output_ext):
    """
    Convert between supported file types using pandas and custom logic.
    """
    if (input_ext, output_ext) == ('.py', '.ipynb'):
        py_to_ipynb(input_path, output_path)
    elif (input_ext, output_ext) == ('.csv', '.json'):
        df = pd.read_csv(input_path)
        df.to_json(output_path, orient='records', lines=True)
    elif (input_ext, output_ext) == ('.json', '.csv'):
        df = pd.read_json(input_path, lines=True)
        df.to_csv(output_path, index=False)
    elif (input_ext, output_ext) == ('.xlsx', '.csv'):
        df = pd.read_excel(input_path)
        df.to_csv(output_path, index=False)
    elif (input_ext, output_ext) == ('.csv', '.xlsx'):
        df = pd.read_csv(input_path)
        df.to_excel(output_path, index=False)
    elif (input_ext, output_ext) == ('.csv', '.parquet'):
        df = pd.read_csv(input_path)
        df.to_parquet(output_path)
    elif (input_ext, output_ext) == ('.parquet', '.csv'):
        df = pd.read_parquet(input_path)
        df.to_csv(output_path, index=False)
    elif (input_ext, output_ext) == ('.csv', '.hdf5'):
        df = pd.read_csv(input_path)
        df.to_hdf(output_path, key='df', mode='w')
    elif (input_ext, output_ext) == ('.hdf5', '.csv'):
        df = pd.read_hdf(input_path)
        df.to_csv(output_path, index=False)
    else:
        raise ValueError('Unsupported conversion')

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...), target_format: str = File(...)):
    """
    Upload a file and convert it to the requested target format.
    Returns file_id and output filename for download.
    """
    input_ext = os.path.splitext(file.filename)[1].lower()
    output_ext = target_format.lower()
    if (input_ext, output_ext) not in SUPPORTED_CONVERSIONS:
        raise HTTPException(status_code=400, detail=f"Conversion from {input_ext} to {output_ext} not supported.")
    file_id = str(uuid.uuid4())
    upload_path = UPLOAD_DIR / f"{file_id}_{file.filename}"
    with open(upload_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    # Use the original filename (without extension) + output_ext for the output file
    base_name = os.path.splitext(file.filename)[0]
    output_name = f"{file_id}_{base_name}{output_ext}"
    output_path = CONVERTED_DIR / output_name
    try:
        convert_file(upload_path, output_path, input_ext, output_ext)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion failed: {e}")
    return {"file_id": file_id, "filename": file.filename, "output_filename": output_name}

@app.get("/download/{file_id}")
async def download_file(file_id: str):
    """
    Download the converted file by file_id.
    Sets Content-Disposition header with correct filename and extension.
    """
    for f in CONVERTED_DIR.iterdir():
        if f.name.startswith(file_id):
            # The output_name is always: {file_id}_{base_name}{output_ext}
            # Remove the file_id and underscore to get the original base name + extension
            output_name = f.name[len(file_id)+1:] if f.name.startswith(file_id + '_') else f.name
            return FileResponse(f, headers={
                "Content-Disposition": f'attachment; filename="{output_name}"'
            })
    raise HTTPException(status_code=404, detail="Converted file not found.")

@app.get("/ping")
def ping():
    """
    Health check endpoint.
    """
    return {"status": "ok"}
