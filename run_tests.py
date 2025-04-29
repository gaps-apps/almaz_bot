import os
import sys

import pytest

from dotenv import load_dotenv



if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
    load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "deploy/.env")))
    pytest.main()
