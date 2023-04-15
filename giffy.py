import logging
import os
from dotenv import load_dotenv
from assistant import GiffyAssistant

# Load env variables
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["SERPAPI_API_KEY"] = os.getenv("SERP_API_KEY")

# Setup logging
log_format = "%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s"
logging.basicConfig(level=logging.INFO, format=log_format, datefmt="%Y-%m-%dT%H:%M:%SZ")

# Get a logger instance
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    gf = GiffyAssistant()
    gf.start()