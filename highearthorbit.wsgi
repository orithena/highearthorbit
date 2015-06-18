import logging, sys
sys.path.insert(0, '/home/dave/Development/highearthorbit')
sys.stdout = sys.stderr
logging.basicConfig(stream=sys.stderr)

from webviewer import app as application
