import sqlite3

conn = sqlite3.connect("finance.db")
cursor = conn.cursor()

username = "admin"
password = "admin123"

# Create user
cursor.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", (username, password))

conn.commit()
conn.close()

print("✅ Admin user created.")
