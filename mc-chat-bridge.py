import os
import time
from queue import Queue
from threading import Thread
import query_mng
import pyautogui

# Path to the Minecraft log file on macOS
#LOG_FILE_PATH = os.path.expanduser(r'/Users/dillon/Library/Application Support/minecraft/logs/latest.log')
LOG_FILE_PATH = os.path.expanduser(r'/Users/dillon/Library/Application Support/minecraft/logs/latest.log')

chat_queue = Queue()

# Function to process chat messages
def process_chat_messages():
    while True:
        message = chat_queue.get()
        if "Dot" in message:
            print(f"Triggering query_mng with query: {message}")
            message = "This is a minecraft chat message" + message 
            context = query_mng.process_query(message)
            response = query_mng.chat_with_gpt(message, context)
            if response:
                print(f"Output from query_mng: {response}")
                send_message(response)

# Function to monitor the log file and filter chat messages
def monitor_log_file():
    with open(LOG_FILE_PATH, 'r') as file:
        file.seek(0, os.SEEK_END)  # Move to the end of the file
        while True:
            line = file.readline()
            if line:
                if '[CHAT]' in line:
                    chat_message = extract_chat_message(line.strip())
                    if chat_message:
                        print(f"Chat message detected: {chat_message}")  # Print chat messages to console
                        chat_queue.put(chat_message)
            time.sleep(0.1)

# Function to extract the username and message from a chat log line
def extract_chat_message(log_line):
    try:
        # Example log line: [HH:MM:SS] [Thread/INFO]: [CHAT] <username> message
        prefix, chat_content = log_line.split('[CHAT] ', 1)
        username, message = chat_content.split('> ', 1)
        username = username.strip('<')
        return f"{username}: {message}"
    except ValueError:
        # If the log line does not match the expected format, return None
        return None

# Function to send a message back to the Minecraft chat
def send_message(message):

    # Open chat
    pyautogui.press('t')
    time.sleep(0.5)  # Wait for the chat to open

    # Type the message and send it
    pyautogui.typewrite(message)
    pyautogui.press('enter')
    print(f"Sent message: {message}")

if __name__ == "__main__":
    # Initialize the database
    query_mng.initialize_db()

    # Start the chat message processor in a separate thread
    thread = Thread(target=process_chat_messages)
    thread.start()

    # Start monitoring the log file
    monitor_log_file()
