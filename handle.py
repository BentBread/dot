import pyautogui
import time
import sys
import subprocess
import os

def execute_commands_from_file(filename):
    with open(filename, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('wait'):
                _, seconds = line.split()
                time.sleep(int(seconds))
            elif line.startswith('key'):
                _, key = line.split()
                press_key(key)
            else:
                execute_baritone_command(line)
                time.sleep(1)  # small delay to ensure command processing

def press_key(key):
    # simulate pressing a key using pyautogui
    print(f"Simulating key press: {key}")
    pyautogui.press(key)

def execute_baritone_command(command):
    # simulate typing the command in the Minecraft chat
    pyautogui.press('t')  # open chat
    pyautogui.typewrite(command)
    pyautogui.press('enter')

def main():
    print("Process started, 10 second timer to wait for setup\n")
    print("Starting chat bridge...\n")
    try:
        script_path = os.path.abspath('mc-chat-bridge.py')
        subprocess.Popen(['cmd.exe', '/c', f'start cmd.exe /K python3 {script_path}'])
    except Exception as e:
        print(f"Exception occurred while running new_script.py: {e}")

    time.sleep(10)
    if len(sys.argv) < 2:
        print("Usage: python script.py <file1> <file2> ...")
        sys.exit(1)
    
    for filename in sys.argv[1:]:
        print(f"Processing file: {filename}")
        execute_commands_from_file(filename)

if __name__ == "__main__":
    main()
