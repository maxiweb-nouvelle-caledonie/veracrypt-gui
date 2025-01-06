import os
import sys

# Ajouter le répertoire temporaire au LD_LIBRARY_PATH
if hasattr(sys, '_MEIPASS'):
    os.environ['LD_LIBRARY_PATH'] = os.pathsep.join([
        os.environ.get('LD_LIBRARY_PATH', ''),
        sys._MEIPASS
    ])
