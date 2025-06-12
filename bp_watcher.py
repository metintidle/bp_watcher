import json
import time
import gui_utils
import subprocess # Added for debug code

# Configuration file path
CONFIG_FILE = "config.json"

def load_config(config_file):
    """Loads configuration from a JSON file."""
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        print(f"Configuration loaded from {config_file}")
        return config
    except FileNotFoundError:
        print(f"Error: Configuration file {config_file} not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {config_file}.")
        return None

def main():
    """Main function to demonstrate GUI automation."""
    print("Starting BP Watcher...")
    config = load_config(CONFIG_FILE)

    if not config:
        print("Exiting due to configuration error.")
        return

    bp_executable_path = config.get("bp_executable_path")
    credentials = config.get("credentials", {})
    login_regions = config.get("login_screen_regions", {})
    server_url = config.get("server_endpoint")
    # screen_regions = config.get("screen_regions", {}) # Keep for general screenshots if needed later

    if not bp_executable_path or not credentials or not login_regions or not server_url:
        print("Error: 'bp_executable_path', 'credentials', 'login_screen_regions', or 'server_endpoint' not fully found in configuration.")
        return

    # Determine process name from executable path (e.g., "notepad.exe" -> "notepad.exe")
    # If path has arguments (e.g., "xterm -T title"), take the first part.
    base_executable = bp_executable_path.split(' ')[0]
    process_name = base_executable.split('/')[-1].split('\\')[-1]

    print(f"Target application full command: {bp_executable_path}")
    print(f"Base executable for process check: {base_executable}")
    print(f"Target process name: {process_name}")

    # Check if the application is running
    if not gui_utils.is_process_running(process_name):
        print(f"{process_name} is not running. Launching application...")
        gui_utils.launch_application(bp_executable_path)
        print("Waiting 10 seconds for application to start and appear...")
        time.sleep(10) # Increased wait time for the application to start

        # --- BEGIN wmctrl DEBUG ---
        print("DEBUG: Listing windows with wmctrl BEFORE find_window...")
        try:
            wmctrl_output = subprocess.run(['wmctrl', '-lG'], capture_output=True, text=True, check=True) # -G for geometry
            print("DEBUG: wmctrl -lG output:\n" + wmctrl_output.stdout)
        except subprocess.CalledProcessError as e:
            print(f"DEBUG: wmctrl -lG failed with error: {e}")
            if e.stderr:
                print(f"DEBUG: wmctrl stderr:\n{e.stderr}")
        except FileNotFoundError:
            print("DEBUG: wmctrl command not found (should not happen if installed).")

        print(f"DEBUG: Checking process status for {process_name}...")
        try:
            ps_output = subprocess.run(['ps', 'aux'], capture_output=True, text=True, check=True)
            gedit_processes = [line for line in ps_output.stdout.split('\n') if process_name in line]
            if gedit_processes:
                print(f"DEBUG: Found gedit process(es):\n" + "\n".join(gedit_processes))
            else:
                print(f"DEBUG: No gedit process found with 'ps aux'.")
        except Exception as e_ps:
            print(f"DEBUG: ps aux command failed: {e_ps}")
        # --- END wmctrl DEBUG ---

    else:
        print(f"{process_name} is already running.")

    # Find the application window
    # For notepad, the title is usually "Untitled - Notepad" or "filename - Notepad"
    # For gedit, it's often "Untitled Document 1" or similar.
    # We'll use a regex that matches the application name or common titles.
    # Adjust window title regex for the application
    if "xterm" in bp_executable_path.lower():
        # The actual title observed for xterm via wmctrl was 'jules@devbox: /app'
        # Let's use a regex that can find part of this, e.g., hostname or typical shell prompt pattern
        window_title_regex = ".*devbox.*" # Matches 'jules@devbox: /app'
    elif "gedit" in bp_executable_path.lower():
        window_title_regex = ".*gedit.*"
    elif "notepad" in bp_executable_path.lower():
        window_title_regex = ".*Notepad.*"
    elif "calc" in bp_executable_path.lower(): # for gnome-calculator or calc.exe
        window_title_regex = ".*Calculator.*"
    else:
        # Default or fallback regex - might need adjustment
        process_name_for_regex = process_name.replace(".exe", "") # Basic removal of .exe
        window_title_regex = f".*{process_name_for_regex}.*"
        print(f"Warning: Specific title regex not set for {bp_executable_path}, using generated: {window_title_regex}")

    print(f"Searching for window with title regex: {window_title_regex}")
    app_window = gui_utils.find_window(window_title_regex)

    if app_window:
        # app_window is now a dict: {'id': '0x...', 'title': 'Actual Window Title'}
        print(f"Application window found: ID={app_window['id']}, Title='{app_window['title']}'")
        if gui_utils.focus_window(app_window): # focus_window now expects this dict
            print("Window focused.")
            time.sleep(0.5) # Wait for focus

            username = credentials.get("username")
            password = credentials.get("password")
            username_coords = login_regions.get("username_field_center")
            password_coords = login_regions.get("password_field_center")
            login_button_coords = login_regions.get("login_button_center")
            success_indicator_region_coords = login_regions.get("login_success_indicator_region")

            data_extraction_config = config.get("data_extraction_regions", {})
            patient_list_coords = data_extraction_config.get("patient_list_area")

            if not all([username, password, username_coords, password_coords, login_button_coords,
                        success_indicator_region_coords, patient_list_coords]):
                print("Error: Missing some credential, login region, or data extraction coordinates from config.")
            else:
                print("Attempting simulated login...")
                if gui_utils.login(username, password, username_coords, password_coords, login_button_coords):
                    print("Login actions (clicks/types) performed by gui_utils.login().")

                    print("Simulating login button action: displaying success message in xterm...")
                    if gui_utils.type_text("echo 'Login OK - Credentials Received'\n", interval=0.05):
                         print("Simulated success message typed.")
                    else:
                        print("Failed to type simulated success message.")
                    time.sleep(1) # Allow time for "Login OK" text to appear

                    print("Attempting to check login success via OCR...")
                    expected_login_text = "Login OK"
                    if gui_utils.check_login_success(success_indicator_region_coords, expected_login_text):
                        print(f"Login check SUCCEEDED: Found '{expected_login_text}'.")

                        # Now simulate displaying patient data
                        print("Simulating display of patient data in xterm...")
                        patient_data_to_display = (
                            "echo -e '\\n\\nPatient Record:\\n"
                            "Name: John Doe\\n"
                            "Phone: 123-456-7890\\n"
                            "Mobile: 098-765-4321\\n"
                            "---\\n"
                            "Patient Record:\\n"
                            "Name: Jane Smith\\n"
                            "Phone: 555-123-4567\\n"
                            "Work: 777-888-9999\\n"
                            "---'\n"
                        )
                        # Clear previous output and display new data by typing 'clear' then the data
                        gui_utils.type_text("clear\n", interval=0.01)
                        time.sleep(0.5)
                        gui_utils.type_text(patient_data_to_display, interval=0.01)
                        time.sleep(1) # Allow text to render

                        print("Attempting to extract and parse patient data...")
                        raw_extracted_text = gui_utils.extract_text_from_region(patient_list_coords)
                        if raw_extracted_text:
                            parsed_patient_data = gui_utils.parse_patient_data_simple(raw_extracted_text)
                            print("Parsed Patient Data:")
                            for record in parsed_patient_data:
                                print(json.dumps(record, indent=2))
                        else:
                            print("No text extracted from patient list area for parsing.")

                        # Send the parsed data to the server
                        if parsed_patient_data: # Ensure there's data to send
                            print(f"Attempting to send {len(parsed_patient_data)} parsed patient record(s) to server: {server_url}")
                            if gui_utils.send_data_to_server(parsed_patient_data, server_url):
                                print("All parsed data sent to server successfully.")
                            else:
                                print("Failed to send some or all parsed data to server.")
                        else:
                            print("No parsed patient data to send to server.")

                    else:
                        print(f"Login check FAILED: Did not find '{expected_login_text}'.")
                else:
                    print("gui_utils.login() function failed to complete all actions.")

            print("Data extraction and server communication demonstration complete.")

        else:
            print(f"Failed to focus the application window: {app_window.get('title', 'Unknown')}")
    else:
        print(f"Application window with title regex '{window_title_regex}' not found after launch.")
        print("Please ensure the application is running and the title regex is correct.")
        # Listing all window titles with wmctrl could be an alternative here for debugging
        # For now, this part is removed as pygetwindow is no longer used for it.
        # try:
        #    all_windows_raw = subprocess.check_output(['wmctrl', '-l'], text=True)
        #    print("Available window titles (from wmctrl -l):")
        #    print(all_windows_raw)
        # except Exception as e:
        #    print(f"Could not get all window titles using wmctrl: {e}")


    print("BP Watcher finished.")
        # Ensure gedit is closed if it was launched by the script.
        # This is tricky because is_process_running checks by name, and we might close a user's gedit.
        # For now, we'll leave it running. In a real scenario, more robust process management is needed.

if __name__ == "__main__":
    main()
