import re
import sqlite3
import os
from openai import OpenAI
from typing_extensions import override
from openai import AssistantEventHandler

DATABASE = 'memory.db'
STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't", "as", "at",
    "be", "because", "been", "before", "being", "below", "between", "both", "but", "by",
    "can't", "cannot", "could", "couldn't",
    "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "even",
    "few", "for", "from", "further",
    "had", "hadn't", "has", "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's",
    "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself",
    "let's", "like",
    "me", "more", "most", "mustn't", "my", "myself",
    "no", "nor", "not",
    "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own",
    "same", "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such",
    "than", "that", "that's", "the", "their", "theirs", "them", "themselves", "then", "there", "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this", "those", "through", "to", "too",
    "under", "until", "up",
    "very",
    "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what", "what's", "when", "when's", "where", "where's", "which", "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would", "wouldn't",
    "you", "you'd", "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves"
}

N = 5  # number of top entries to fetch for context

def initialize_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS words (word TEXT PRIMARY KEY)")
    conn.commit()
    conn.close()

def get_db_connection():
    return sqlite3.connect(DATABASE)

def process_query(query):
    words = query.split()
    context = []
    conn = get_db_connection()
    cursor = conn.cursor()

    for word in words:
        if word not in STOP_WORDS:
            cursor.execute("INSERT OR IGNORE INTO words (word) VALUES (?)", (word,))
            table_name = f'"{word}"'
            cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (value INTEGER, data TEXT)")
            cursor.execute(f"SELECT value, data FROM {table_name} ORDER BY value DESC LIMIT ?", (N,))
            top_entries = cursor.fetchall()

            if top_entries:
                max_value = top_entries[0][0]
                cursor.execute(f"INSERT INTO {table_name} (value, data) VALUES (?, ?)", (max_value + 1, query))
                for value, data in top_entries:
                    cursor.execute(f"UPDATE {table_name} SET value = value + 1 WHERE data = ?", (data,))
            else:
                cursor.execute(f"INSERT INTO {table_name} (value, data) VALUES (?, ?)", (1, query))

            context.extend([data for value, data in top_entries])

    conn.commit()
    conn.close()
    return context

def chat_with_gpt(query, context):
    context_str = ' '.join(context)
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable is not set")
        return

    client = OpenAI(api_key=api_key)

    # Replace with your existing assistant's ID
    assistant_id = 'asst_iIp9Nr1q3U4UaXeGXmfZkEhR'  # Replace this with your assistant's ID

    # Create a Thread
    thread = client.beta.threads.create()

    # Add a Message to the Thread
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=query
    )

    # Variable to store the response
    response_text = []

    # EventHandler for streaming response
    class EventHandler(AssistantEventHandler):    
        @override
        def on_text_created(self, text) -> None:
            response_text.append(str(text))
      
        @override
        def on_text_delta(self, delta, snapshot):
            response_text.append(str(delta.value))
      
        def on_tool_call_created(self, tool_call):
            response_text.append(f"\nassistant > {tool_call.type}\n")
  
        def on_tool_call_delta(self, delta, snapshot):
            if delta.type == 'code_interpreter':
                if delta.code_interpreter.input:
                    response_text.append(str(delta.code_interpreter.input))
                if delta.code_interpreter.outputs:
                    response_text.append(f"\n\noutput >")
                    for output in delta.code_interpreter.outputs:
                        if output.type == "logs":
                            response_text.append(str(output.logs))

    # Stream the response
    with client.beta.threads.runs.stream(
        thread_id=thread.id,
        assistant_id=assistant_id,
        event_handler=EventHandler(),
    ) as stream:
        stream.until_done()
    
    # Join and clean up the collected response
    raw_response = ''.join(response_text)
    
    # Clean up metadata
    clean_response = re.sub(r'Text\(.*?\)', '', raw_response)  # Remove 'Text(...)'
    clean_response = re.sub(r'\[.*?\]', '', clean_response)  # Remove square-bracketed references
    clean_response = re.sub(r'\nassistant >.*?\n', '', clean_response)  # Remove assistant tool calls
    
    return clean_response.strip()
def main():
    initialize_db()
    
    while True:

   
        query = input("Enter your query: ")
        context = process_query(query)
        response = chat_with_gpt(query, context)
        if response:
            print(f"Output from query_mng: {response}")


if __name__ == "__main__":
    main()