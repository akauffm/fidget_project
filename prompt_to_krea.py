import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import xmlrpc.client
from simple_rpc import Interface

rpc_port = "8050"
rpc = xmlrpc.client.ServerProxy(f"http://localhost:{rpc_port}")

# --- Configuration ---
PROMPT_TEXT = ""
start_text = ""
last_text_spoken = ""
slider_value = 0
last_slider_value = 0

interface = Interface('/dev/cu.usbmodem1101')

def set_slider_value(driver, slider_id, target_value):
    """
    Sets a slider's value using JavaScript.

    Args:
        driver: The Selenium WebDriver instance.
        slider_id: The ID of the slider <input> element.
        target_value: The desired value to set (as a string or number).
    """
    # Find the slider element
    slider = driver.find_element(By.ID, slider_id)
    
    # The JavaScript to execute
    # arguments[0] is the first element passed (our slider)
    # arguments[1] is the second argument (the target value)
    script = """
    arguments[0].value = arguments[1];
    arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
    arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
    """
    
    # Execute the script
    driver.execute_script(script, slider, str(target_value))


# -- Connect to Chrome --
try:
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    print("🔌 Connecting to the dedicated automation browser...")
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
    print("✔  Successfully connected to browser!")

    # Find the textarea once
    wait = WebDriverWait(driver, 20)
    textarea_locator = (By.XPATH, '//textarea[@placeholder="Describe an image and click generate..."]')
    print("🔎 Finding the prompt textarea on the page...")
    prompt_textarea = wait.until(EC.element_to_be_clickable(textarea_locator))
    print("✔  Textarea found. Ready to receive prompts.")
except WebDriverException:
    print("\n❌ FATAL: Could not connect to the Chrome browser.")
    print("   Please ensure you launched Chrome with the --remote-debugging-port=9222 flag.")
except Exception as e:
    print(f"\n❌ FATAL: Could not find the Krea.ai textarea. {e}")
    print("   Please ensure the correct page is open in the automation browser.")

# --- Main Script ---
try:
    while True:
        # Read Arduino value
        slider_value = interface.getPotValue();

        if slider_value != last_slider_value:
            print("Slider value:" + str(slider_value))
            normalized_value = 0.35 + ((slider_value - 0) / (1023 - 0)) * (1 - 0.35)

            try:
                set_slider_value(driver, "myRange", normalized_value)
                print(f"Successfully set slider 'myRange' to {normalized_value}")
            except Exception as e:
                print(f"An error occurred: {e}")
            
        last_slider_value = slider_value

        # Fetch the prompt from your server
        if len(rpc.getPrompt()) > 1:
            in_text = rpc.getPrompt()
            print(in_text)
            if in_text != PROMPT_TEXT:
                PROMPT_TEXT = in_text
        else:
            if PROMPT_TEXT != start_text:
                PROMPT_TEXT = start_text

        if PROMPT_TEXT != last_text_spoken:
            try:
                # Update the textarea in the browser
                prompt_textarea.clear()
                prompt_textarea.send_keys(PROMPT_TEXT)         
                print("✔  Browser updated successfully.")

            except StaleElementReferenceException:
                # This happens if the page reloaded or the element was redrawn
                print("   [Warning] Page element became stale. Re-finding textarea...")
                prompt_textarea = wait.until(EC.element_to_be_clickable(textarea_locator))
                # We will retry on the next loop iteration
            except Exception as e:
                print(f"   [Error] Could not update browser textarea: {e}")

        # Wait for the configured interval before checking again
        time.sleep(.25)

except KeyboardInterrupt:
    sys.exit(0)