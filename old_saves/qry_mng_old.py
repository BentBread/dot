import sqlite3
import os
from openai import OpenAI

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
            cursor.execute(f"SELECT value FROM {table_name} ORDER BY value DESC LIMIT {N}")
            top_values = cursor.fetchall()
            if len(top_values) >= N:
                value_for_new_entry = top_values[N-1][0]
            else:
                value_for_new_entry = 1

            cursor.execute(f"INSERT INTO {table_name} (value, data) VALUES (?, ?)", (value_for_new_entry, query))
            
            cursor.execute(f"SELECT value, data FROM {table_name} ORDER BY value DESC LIMIT {N}")
            top_entries = cursor.fetchall()

            context.extend([data for value, data in top_entries])

    conn.commit()
    conn.close()
    return context

def add_entry(word, value, data):
    conn = get_db_connection()
    cursor = conn.cursor()
    table_name = f'"{word}"'
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (value INTEGER, data TEXT)")
    cursor.execute(f"INSERT INTO {table_name} (value, data) VALUES (?, ?)", (value, data))
    conn.commit()
    conn.close()

def view_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT word FROM words")
    words = cursor.fetchall()

    for (word,) in words:
        print(f"Word: {word}")
        table_name = f'"{word}"'
        cursor.execute(f"SELECT value, data FROM {table_name} ORDER BY value DESC LIMIT {N}")
        entries = cursor.fetchall()
        for value, data in entries:
            print(f"  Value: {value}, Data: {data}")

    conn.close()

def chat_with_gpt(query, context):
    context_str = ' '.join(context)
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable is not set")
        return

    client = OpenAI(api_key=api_key)
    model = "ft:gpt-3.5-turbo-1106:personal::9NZDkpmR"
    params = f'You are Dot, an assistant for Dillon, you are smart, wise and simple. you have multiple interfaces including minecraft, robot, chatbot, ect. You will be provided context with every query, some of it may be relevent some not, use as needed Context: {context_str}'
    messages = [
        {"role": "system", "content": params},
        {"role": "user", "content": query},
    ]

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0
        )

        response_message = response.choices[0].message.content
        print(response_message)
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")

def main():
    initialize_db()
    
    while True:
        #print("Options: [1] Process Query [2] Add Entry [3] View Database [4] Exit")
        #choice = input("Choose an option: ")
        choice = 1
        if choice == '1':
            query = input("Enter your query: ")
            context = process_query(query)
            chat_with_gpt(query, context)
        elif choice == '2':
            word = input("Enter word: ")
            value = int(input("Enter value: "))
            data = input("Enter data: ")
            add_entry(word, value, data)
        elif choice == '3':
            view_database()
        elif choice == '4':
            break
        else:
            print("Invalid choice. Try again.")

if __name__ == "__main__":
    main()
