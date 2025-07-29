# Team Dream
These are all the pieces required to get camera- and voice-driven real-time diffusion running. It uses [Krea](https://krea.ai/realtime) for the image generation, a local speech detector based on [Kat's edge voice agent](https://github.com/ktomanek/edge_voice_agent) for the speech-to-text, and a [slide pot](https://www.aliexpress.us/item/3256806546906210.html) hooked up to an Arduino for the physical control.

(There's a full write-up of the project with more videos [here](https://quiptic.com/team-dream/))

**(Make sure the sound is on)**

https://github.com/user-attachments/assets/467fe273-9cbc-4525-9042-92d0bddd8b7f

## Installation
(I'm going to write out every step, forgive me if it's overkill)

1. ```git clone https://github.com/akauffm/fidget_project && cd fidget_project/modular_voice```
2. ```python -m venv venv```
3. ```source venv/bin/activate```
4. ```pip install -r requirements.txt```
5. ```pip install useful-moonshine-onnx@git+https://git@github.com/usefulsensors/moonshine.git#subdirectory=moonshine-onnx```
  
## Run everything
1. In a new terminal window, run ```/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir="$HOME/AutomationProfile"``` That starts up a fresh Chrome browser instance so (big deal if you have as many open tabs as I do).
    1. Accept the terms
    2. Navigate to krea.ai/realtime
    3. Click on the webcam button and agree to the permissions popup
2. In a new terminal window, run ```python rpc.py```
3. In a new terminal window, run ```python live_captions.py --use_rpc```
4. In a new terminal window, run ```cd .. && python prompt_to_krea.py``` If you add ```--use_arduino /dev/WHATEVER_PORT``` it'll listen for the slider.



