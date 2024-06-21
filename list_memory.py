import sqlite3

DATABASE = 'memory.db'
N = 5  # number of top entries to fetch for context

def list_memory_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT word FROM words")
    words = cursor.fetchall()
    
    for (word,) in words:
        print(f"Word: {word}")
        table_name = f'"{word}"'
        cursor.execute(f"SELECT value, data FROM {table_name} ORDER BY value DESC LIMIT ?", (N,))
        entries = cursor.fetchall()
        for value, data in entries:
            print(f"  Value: {value}, Data: {data}")
    
    conn.close()

if __name__ == "__main__":
    list_memory_db()
