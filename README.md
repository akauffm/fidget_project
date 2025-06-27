# Installing all this
(I'm going to write out every step, forgive me it it's overkill)

1. ```git clone https://github.com/akauffm/fidget_project $$ cd fidget_project/modular_voice```
2. ```python -m venv venv```
3. ```source venv/bin/activate```
4. ```pip install -r requirements.txt```
5. ```pip install useful-moonshine-onnx@git+https://git@github.com/usefulsensors/moonshine.git#subdirectory=moonshine-onnx```
  
## You should now be ready to run everything
1. In a new terminal window, run ```/Applications/Google\ Chrome.app/Contents/MacOS/Gole\ Chrome --remote-debugging-port=9222 --user-data-dir="$HOME/AutomationProfile"``` That starts up a fresh Chrome browser.
    1. Accept the terms
    2. Navigate to krea.ai/realtime
    3. Click on the webcam button and agree to the permissions popup
2. In a new terminal window, run ```python rpc.py```
3. In a new terminal window, run ```python live_captions.py --use_rpc```
4. In a new terminal window, run ```cd .. && python prompt_to_krea.py``` If you add ```--use_arduino /dev/WHATEVER_PORT``` it'll listen for the slider.

## I'm nearly 100% certain I've missed something, but give it a try and let me know if you run into issues.
