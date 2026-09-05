import sqlite3
import json

db_path = "c:/Users/Shraddha/Desktop/Qickdock_Seo/backend/data/qicdock.db"

try:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, content_type, image_prompt, image_prompts 
        FROM calendar_entries 
        WHERE content_type = 'carousel'
        ORDER BY id DESC LIMIT 5
    """)
    rows = cursor.fetchall()
    
    for row in rows:
        print(f"ID: {row['id']}")
        print(f"Content Type: {row['content_type']}")
        print(f"Image Prompt: {row['image_prompt'][:50]}...")
        print(f"Image Prompts: {row['image_prompts']}")
        print("-" * 40)
        
    conn.close()
except Exception as e:
    print(f"Error: {e}")
