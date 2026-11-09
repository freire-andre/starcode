import os, sys
sys.exit(0 if os.path.basename(os.getcwd()) == "sub" else 1)
