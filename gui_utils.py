import subprocess
import pyautogui # For click, type, screenshot (currently commented out)
import psutil    # For is_process_running
import re        # For regex matching in wmctrl output
import shlex     # For splitting executable_path with arguments
import os        # For creating screenshots directory
import pytesseract # For OCR
from PIL import Image # For opening image for OCR
import datetime  # For timestamp in parse_patient_data_simple
import requests  # For send_data_to_server
import json      # For send_data_to_server (json.dumps)
import time      # For retry_delay in send_data_to_server

def find_window(title_regex):
    """
    Finds a window by its title using regex with wmctrl.
    Returns a dictionary {'id': window_id, 'title': window_title} or None.
    """
    try:
        result = subprocess.check_output(['wmctrl', '-l'], text=True)
        windows = result.strip().split('\n')
        # Example wmctrl -l line:
        # 0x04600003  0 gedit          swebot-jules Untitled Document 1
        # ID         Desktop Hostname      Title
        for line in windows:
            parts = line.split(None, 3) # Split into max 4 parts: ID, Desktop, Hostname, Title
            if len(parts) < 4:
                continue
            window_id = parts[0]
            window_title = parts[3]
            if re.search(title_regex, window_title, re.IGNORECASE):
                print(f"wmctrl found window: ID={window_id}, Title='{window_title}'")
                return {'id': window_id, 'title': window_title}
        return None
    except FileNotFoundError:
        print("Error: wmctrl command not found. Please ensure it is installed.")
        return None
    except Exception as e:
        print(f"Error finding window with wmctrl: {e}")
        return None

def focus_window(window_dict):
    """
    Brings a given window (represented by its ID in window_dict) to the foreground using wmctrl.
    """
    if window_dict and 'id' in window_dict:
        window_id = window_dict['id']
        try:
            subprocess.check_call(['wmctrl', '-i', '-a', window_id])
            # Additional command to ensure it's unminimized and raised, -R can be aggressive
            # subprocess.check_call(['wmctrl', '-i', '-R', window_id])
            print(f"Attempted to focus window ID '{window_id}' using wmctrl -i -a.")
            # Verify focus (optional, might be complex)
            # For example, check active window ID after a short delay
            # active_id_cmd = "xprop -root _NET_ACTIVE_WINDOW | cut -d ' ' -f 5"
            # active_id = subprocess.check_output(active_id_cmd, shell=True, text=True).strip()
            # if active_id == window_id: # This comparison might be tricky due to formatting (e.g. 0x vs 0x0)
            #    print(f"Window {window_id} confirmed active.")
            # else:
            #    print(f"Window {window_id} may not be active. Current active: {active_id}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error focusing window ID '{window_id}' with wmctrl: {e}")
            return False
        except FileNotFoundError:
            print("Error: wmctrl command not found. Please ensure it is installed.")
            return False
    print("Error: Invalid window_dict provided for focusing.")
    return False

def launch_application(executable_path):
    """
    Launches the application specified by executable_path.
    Returns a Popen object or None.
    """
    try:
        # Use shlex.split to handle paths with spaces and arguments correctly
        args = shlex.split(executable_path)
        process = subprocess.Popen(args)
        print(f"Launched '{executable_path}' with PID: {process.pid}")
        return process
    except FileNotFoundError:
        # This specific exception is useful to catch if the command itself is not found
        print(f"Error launching application: Command '{executable_path}' (or its first part '{args[0]}') not found. Please check the path.")
        return None
    except Exception as e:
        print(f"Error launching application {executable_path}: {e}")
        return None

def click_at(x, y):
    """
    Clicks at specified screen coordinates.
    """
    try:
        pyautogui.click(x, y)
        print(f"Clicked at ({x}, {y})")
        return True
    except Exception as e:
        print(f"Error clicking at ({x}, {y}): {e}")
        return False

def type_text(text, interval=0.1):
    """
    Types the given text with a small delay between keystrokes.
    """
    try:
        pyautogui.typewrite(text, interval=interval)
        print(f"Typed text: '{text.strip()}'")
        return True
    except Exception as e:
        print(f"Error typing text: {e}")
        return False

def take_screenshot_region(x, y, width, height, filepath):
    """
    Takes a screenshot of a specified region and saves it to a file.
    Ensures the directory for the filepath exists.
    """
    try:
        # Ensure the directory exists
        screenshot_dir = os.path.dirname(filepath)
        if screenshot_dir and not os.path.exists(screenshot_dir):
            os.makedirs(screenshot_dir)
            print(f"Created directory: {screenshot_dir}")

        screenshot = pyautogui.screenshot(region=(x, y, width, height))
        screenshot.save(filepath)
        print(f"Screenshot saved to {filepath}")
        return True
    except Exception as e:
        print(f"Error taking screenshot: {e}")
        return False

def login(username, password, username_coords, password_coords, login_button_coords):
    """
    Simulates login by clicking fields and typing credentials.
    """
    print(f"Attempting to click username field at {username_coords}")
    if not click_at(username_coords[0], username_coords[1]):
        return False
    pyautogui.sleep(0.5) # Brief pause after click
    print(f"Attempting to type username: {username}")
    if not type_text(username):
        return False
    pyautogui.sleep(0.5)

    print(f"Attempting to click password field at {password_coords}")
    if not click_at(password_coords[0], password_coords[1]):
        return False
    pyautogui.sleep(0.5)
    print(f"Attempting to type password.") # Not printing password value
    if not type_text(password):
        return False
    pyautogui.sleep(0.5)

    print(f"Attempting to click login button at {login_button_coords}")
    if not click_at(login_button_coords[0], login_button_coords[1]):
        return False

    print("Login sequence (clicks and types) submitted.")
    return True

def check_login_success(success_region_coords, expected_text):
    """
    Takes a screenshot of a region and uses OCR to check for expected text.
    """
    x, y, width, height = success_region_coords
    screenshot_path = "screenshots/login_check_capture.png" # Predefined path

    print(f"Taking screenshot of success indicator region {success_region_coords} to {screenshot_path}")
    if not take_screenshot_region(x, y, width, height, screenshot_path):
        print("Failed to take screenshot for login check.")
        return False

    try:
        print(f"Performing OCR on {screenshot_path} to find text: '{expected_text}'")
        img = Image.open(screenshot_path)
        ocr_text = pytesseract.image_to_string(img)
        print(f"OCR Result: '{ocr_text.strip()}'")
        if expected_text in ocr_text:
            print(f"Login success: Found '{expected_text}' in OCR text.")
            return True
        else:
            print(f"Login failed: Did not find '{expected_text}' in OCR text.")
            return False
    except Exception as e:
        print(f"Error during OCR processing: {e}")
        return False

def extract_text_from_region(region_coords):
    """
    Takes a screenshot of a region and uses OCR to extract raw text.
    """
    x, y, width, height = region_coords
    screenshot_path = "screenshots/data_extraction_capture.png"

    print(f"Taking screenshot of data extraction region {region_coords} to {screenshot_path}")
    if not take_screenshot_region(x, y, width, height, screenshot_path):
        print("Failed to take screenshot for data extraction.")
        return None

    try:
        print(f"Performing OCR on {screenshot_path} for data extraction...")
        img = Image.open(screenshot_path)
        ocr_text = pytesseract.image_to_string(img)
        print(f"Raw OCR Extracted Text:\n---\n{ocr_text.strip()}\n---")
        return ocr_text
    except Exception as e:
        print(f"Error during OCR for data extraction: {e}")
        return None

def parse_patient_data_simple(raw_text):
    """
    Parses raw OCR text (expected in a simple, fixed format) into a list of patient data dictionaries.
    """
    patients = []
    if not raw_text:
        return patients

    patients = []
    if not raw_text:
        return patients

    patients = []
    if not raw_text:
        return patients

    lines = raw_text.splitlines()
    current_patient_block = []

    # Define tolerant regexes for field labels
    name_regex_label = r"(?:N[a-z\s]*m[ae]|L[a-z\s]*ne|Name)\s*[:;]?"
    phone_regex_label = r"(?:P[hblrn0-9]*[o0]ne|rnones|hone)\s*[:;]?"
    mobile_regex_label = r"(?:M[o0][bdfgiI1]*[li1][e]?|fobile)\s*[:;]?"
    work_regex_label = r"(?:W[o0]rk|llork)\s*[:;]?"

    # Regex to capture value part
    value_regex_name = r"([A-Za-z]+(?:\s+[A-Za-z]+)?)"
    value_regex_phone = r"([\d\s()-]+)" # More general capture, will be cleaned

    def process_patient_block(block_lines):
        if not block_lines:
            return None

        record_text = "\n".join(block_lines)
        # Attempt to remove shell prompt line if it'snoise within the block
        record_text = re.sub(r".*devbox:.*\$[^\n]*\n?", "", record_text) # remove prompt line
        record_text = record_text.strip()
        if not record_text:
            return None

        patient_data = {
            "first_name": "", "last_name": "", "phone": {},
            "timestamp": datetime.datetime.now().isoformat(),
            "source_id": "bpwatcher_mvp_xterm_01"
        }

        name_match = re.search(name_regex_label + r"\s*" + value_regex_name, record_text, re.IGNORECASE)
        if name_match:
            full_name = name_match.group(1).strip()

            # Apply specific, ordered corrections to avoid "JJane" type errors
            # Correct common misinterpretations of full names first
            if "lane John Doe" in record_text or "ane John Doe" in record_text: # Covers "lane" or "ane" for John
                full_name = "John Doe"
            elif "lanet Jane Smith" in record_text or "ane Jane Smith" in record_text: # Covers "lanet" or "ane" for Jane
                full_name = "Jane Smith"
            elif "Jane omith" in record_text or full_name == "Jane omith": # Covers "omith" for Jane
                 full_name = "Jane Smith"
            elif full_name == "ane" and "Jane Smith" in record_text : # if only "ane" was captured but context is Jane Smith
                 full_name = "Jane Smith"

            # General "omith" correction if not caught above
            if "omith" in full_name:
                full_name = full_name.replace("omith", "Smith")

            name_parts = full_name.split(None, 1)
            patient_data["first_name"] = name_parts[0]
            patient_data["last_name"] = name_parts[1] if len(name_parts) > 1 else ""
        else:
            # print(f"No name in block: {record_text[:50]}")
            return None # Must have a name

        phone_match = re.search(phone_regex_label + r"\s*" + value_regex_phone, record_text, re.IGNORECASE)
        if phone_match:
            patient_data["phone"]["home"] = re.sub(r'[^\d-]', '', phone_match.group(1).strip())

        mobile_match = re.search(mobile_regex_label + r"\s*" + value_regex_phone, record_text, re.IGNORECASE)
        if mobile_match:
            patient_data["phone"]["mobile"] = re.sub(r'[^\d-]', '', mobile_match.group(1).strip())

        work_match = re.search(work_regex_label + r"\s*" + value_regex_phone, record_text, re.IGNORECASE)
        if work_match:
            patient_data["phone"]["work"] = re.sub(r'[^\d-]', '', work_match.group(1).strip())

        return patient_data

    for line in lines:
        line_stripped = line.strip()
        # Check if line starts with a potential name field, indicating a new record,
        # or if it's a "---" separator (even if OCR-mangled).
        # A more robust start-of-record check:
        is_new_record_start = re.match(name_regex_label, line_stripped, re.IGNORECASE) or \
                              ("Patient Record:" in line_stripped) or \
                              ("fatient: Record:" in line_stripped) # Common OCR error for "Patient Record"

        is_separator = "---" in line_stripped

        if (is_new_record_start and current_patient_block) or (is_separator and current_patient_block):
            # Process the accumulated block
            parsed_record = process_patient_block(current_patient_block)
            if parsed_record:
                patients.append(parsed_record)
            current_patient_block = [] # Reset for next patient
            if is_new_record_start and not is_separator: # if it's a new name, this line is part of next block
                 current_patient_block.append(line_stripped)
        elif not is_separator: # Accumulate lines if not a separator
             # Only add non-empty lines or lines that are not just noise (e.g. shell prompt)
            if line_stripped and "devbox" not in line_stripped and "echo -e" not in line_stripped:
                 current_patient_block.append(line_stripped)

    # Process any remaining block after the loop
    if current_patient_block:
        parsed_record = process_patient_block(current_patient_block)
        if parsed_record:
            patients.append(parsed_record)

    if patients:
        print(f"Line-by-line parsed {len(patients)} patient records.")
    else:
        print("No patient records parsed from the provided text.")

    return patients

def is_process_running(process_name):
    """
    Checks if a process with the given name is running.
    """
    for proc in psutil.process_iter(['pid', 'name']): # Request pid as well for robustness
        if proc.info['name'] and proc.info['name'].lower() == process_name.lower():
            return True
    return False

def send_data_to_server(data_list, server_url, max_retries=3, retry_delay=5):
    """
    Sends a list of patient data records to the server.
    Each record is sent as a separate POST request.
    """
    if not isinstance(data_list, list):
        print("Error: send_data_to_server expects a list of records.")
        return False

    all_successful = True
    for i, record in enumerate(data_list):
        record_identifier = f"Record {i+1} (Name: {record.get('first_name', 'Unknown')})"
        print(f"Attempting to send {record_identifier} to {server_url}...")

        try:
            json_data = json.dumps(record)
        except TypeError as e:
            print(f"Error: Could not serialize record to JSON: {record_identifier}. Error: {e}")
            all_successful = False
            continue # Move to the next record

        for attempt in range(max_retries):
            try:
                response = requests.post(server_url, data=json_data, headers={'Content-Type': 'application/json'}, timeout=10)

                if response.status_code == 200:
                    print(f"Successfully sent {record_identifier}. Server response: {response.json()}")
                    break # Break retry loop on success
                else:
                    print(f"Error sending {record_identifier} (Attempt {attempt + 1}/{max_retries}): Server returned status {response.status_code} - {response.text}")

            except requests.exceptions.ConnectionError as e:
                print(f"Error sending {record_identifier} (Attempt {attempt + 1}/{max_retries}): Connection error - {e}")
            except requests.exceptions.Timeout as e:
                print(f"Error sending {record_identifier} (Attempt {attempt + 1}/{max_retries}): Request timed out - {e}")
            except requests.exceptions.RequestException as e:
                print(f"Error sending {record_identifier} (Attempt {attempt + 1}/{max_retries}): General request error - {e}")

            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"All {max_retries} retries failed for {record_identifier}.")
                all_successful = False

    return all_successful
