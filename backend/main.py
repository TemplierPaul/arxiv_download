import os
import shutil
import tarfile
import re
import requests
import tempfile
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
from pylatexenc.latex2text import LatexNodes2Text

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

OUTPUT_BASE = Path("/output")

class PaperRequest(BaseModel):
    url: str
    algo_name: str

def get_arxiv_id(url: str):
    match = re.search(r"(\d+\.\d+)", url)
    if not match:
        raise ValueError("Could not find ArXiv ID in URL")
    return match.group(1)

def clean_latex(latex_content: str) -> str:
    """
    Uses pylatexenc to parse LaTeX and convert to plain text.
    """
    try:
        # math_mode='text' keeps math symbols but tries to use unicode
        converter = LatexNodes2Text(math_mode='text', keep_comments=False)
        text = converter.latex_to_text(latex_content)
        
        # Cleanup whitespace
        text = re.sub(r'\n{3,}', '\n\n', text) 
        text = re.sub(r'[ \t]+', ' ', text)
        return text.strip()
    except Exception as e:
        print(f"Warning: pylatexenc failed: {e}. Falling back to basic strip.")
        lines = [l for l in latex_content.split('\n') if not l.strip().startswith('%')]
        return '\n'.join(lines)

@app.post("/process")
async def process_paper(req: PaperRequest):
    temp_dir = None
    target_dir = None
    try:
        arxiv_id = get_arxiv_id(req.url)
        safe_name = "".join([c for c in req.algo_name if c.isalnum() or c in ('-','_')])
        
        target_dir = OUTPUT_BASE / safe_name
        
        # 1. Clean start for target directory
        if target_dir.exists():
            shutil.rmtree(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # 2. Use a temporary directory for extraction
        temp_dir = Path(tempfile.mkdtemp())
        
        print(f"Downloading source for {arxiv_id}...")
        source_url = f"https://arxiv.org/e-print/{arxiv_id}"
        response = requests.get(source_url, stream=True)
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Could not download from ArXiv")

        tar_path = temp_dir / "source.tar.gz"
        with open(tar_path, "wb") as f:
            f.write(response.content)

        # 3. Extract to temp
        try:
            with tarfile.open(tar_path) as tar:
                def is_safe(members):
                    for member in members:
                        if member.name.startswith('/') or '..' in member.name:
                            continue
                        yield member
                tar.extractall(path=temp_dir, members=is_safe(tar))
        except tarfile.ReadError:
            pass

        # 4. Process files
        tex_files_found = list(temp_dir.rglob("*.tex"))
        full_text_content = []

        for tex_source in tex_files_found:
            dest = target_dir / tex_source.name
            
            # Handle filename collisions
            if dest.exists():
                new_name = f"{tex_source.parent.name}_{tex_source.name}"
                dest = target_dir / new_name

            try:
                # Read RAW
                with open(tex_source, 'r', encoding='utf-8', errors='ignore') as f:
                    raw_content = f.read()
                
                # CLEAN
                cleaned_text = clean_latex(raw_content)
                
                # Write CLEAN INDIVIDUAL file
                with open(dest, 'w', encoding='utf-8') as f:
                    f.write(cleaned_text)

                # Append to AGGREGATE list with Markdown formatting
                header = f"# File: {dest.name}"
                full_text_content.append(f"{header}\n\n{cleaned_text}\n")
                    
            except Exception as e:
                print(f"Skipping processing of {tex_source.name}: {e}")

        # 5. Write the AGGREGATE file as Markdown
        with open(target_dir / "_full_paper_context.md", "w", encoding='utf-8') as f:
            # Use a horizontal rule between files for cleaner LLM ingestion
            f.write("\n---\n\n".join(full_text_content))

        return {"status": "success", "path": str(target_dir), "files_found": len(tex_files_found)}

    except Exception as e:
        print(f"Error: {e}")
        if target_dir and target_dir.exists():
             shutil.rmtree(target_dir)
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        if temp_dir and temp_dir.exists():
            shutil.rmtree(temp_dir)