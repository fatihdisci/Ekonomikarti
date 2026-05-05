import os
from pathlib import Path
from PIL import Image
from src.pipeline import run_morning

def test_render_dry_run():
    # Ensure the output directory is clean if needed, though run_morning will overwrite
    output_path = run_morning(dry_run=True)
    
    # Check if PNG exists
    assert output_path.exists()
    assert output_path.suffix == ".png"
    
    # Check dimensions (1080x1350)
    with Image.open(output_path) as img:
        assert img.size == (1080, 1350)
    
    # Check if caption.txt was generated in the same directory
    caption_path = output_path.parent / "caption.txt"
    assert caption_path.exists()
    
    content = caption_path.read_text(encoding="utf-8")
    assert "#fiyathafizasi" in content
