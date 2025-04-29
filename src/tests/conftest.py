from dotenv import load_dotenv
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "../deploy/.env")))
