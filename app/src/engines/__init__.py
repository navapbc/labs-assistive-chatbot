# Register engine subclasses so they are discovered by
# chat_engine.available_engines() via all_subclasses(ChatEngineInterface).
#
# To add a new engine:
#   1. Create a new file in this directory (e.g., my_engine.py)
#   2. Define a subclass of BaseEngine with a unique engine_id
#   3. Import the module here (e.g., import src.engines.my_engine)

import src.engines.example_engine  # noqa: F401
