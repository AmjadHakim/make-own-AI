#!/usr/bin/env python
import sys
import argparse
from pathlib import Path

# Add the project directory to Python path
project_root = Path(__file__).parent.absolute()
sys.path.append(str(project_root))

# Now we can import our main module
from src.main import main

if __name__ == "__main__":
    # The main module will handle the command line arguments
    main()
