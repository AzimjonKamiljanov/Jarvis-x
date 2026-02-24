#!/bin/bash
# Downloads the small English Vosk model
set -e

mkdir -p models
cd models

if [ ! -d "vosk-model-small-en-us-0.15" ]; then
    echo "Downloading Vosk English model..."
    wget -q https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
    unzip -q vosk-model-small-en-us-0.15.zip
    ln -sf vosk-model-small-en-us-0.15 vosk-model-small-en-us
    rm vosk-model-small-en-us-0.15.zip
    echo "✅ Model downloaded successfully!"
else
    echo "Model already exists."
fi
