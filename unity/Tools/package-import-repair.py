"""Compatibility entry point: the old repair download now includes all restoration dependencies."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).with_name('package-update.py')),run_name='__main__')
