#!/bin/bash
echo "Reinstalling groq package..."
pip uninstall -y groq
pip install --upgrade groq
echo "Done! Please restart the server."
