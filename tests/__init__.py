# This file makes Python treat the directory tests as a package.
# You can add common test setup or fixtures here if needed.

import sys
import os

# Add src directory to sys.path for tests to find modules
# This assumes tests are run from the project root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)
