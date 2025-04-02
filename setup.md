## Setting up the python

1. Start python environment
   a. Create the python environment by typing `python -m venv venv` in terminal in the correct directory (most likely backend)  
   b. You should be able to run with a line like `venv\Scripts\activate` but I've had problems with this in the past. This new line should make it work without issue: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and `.\venv\Scripts\Activate.ps1`.

2. Beyond that, you can run `pip install requirements.txt` to get all the python libraries used.

## Setting up FastAPI

# Set up kaggle API
