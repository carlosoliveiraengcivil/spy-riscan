"""
SPY RiSCAN - Auditor de Inventários Volumétricos
Ponto de entrada principal.
Desenvolvido por Carlos Oliveira
"""

import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from app_gui import SpyRiSCANApp


def main():
    app = SpyRiSCANApp()
    app.run()


if __name__ == "__main__":
    main()
