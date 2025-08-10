import os
EPHE_PATH = os.environ.get("SWISS_EPHE_PATH") or os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "ephe")
