#!/bin/bash
cd /Users/semihsahin58/Desktop/dilaram/AlisverisAsistani
export DYLD_LIBRARY_PATH="/opt/homebrew/opt/expat/lib:$DYLD_LIBRARY_PATH"
source venv/bin/activate
python3 ShoppingAssistant.py
