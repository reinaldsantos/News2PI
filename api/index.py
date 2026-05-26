import sys
import os
from pathlib import Path

root_dir = str(Path(__file__).resolve().parent.parent)
sys.path.append(root_dir)
os.chdir(root_dir)

from main import app
