#!/bin/bash
cd /home/jakekausler/programs/FlashcardServer/
python3 server.py 2>&1 | tee -a /home/jakekausler/tmp/output
