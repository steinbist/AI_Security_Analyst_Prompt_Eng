import sqlite3, bcrypt, getpass, pathlib, datetime, sys

# Path to your app.db file
db = pathlib.Path("app/data/app.db")

try:
    # Prompt for username and password
    username = input("Enter new username: ").strip()
    if not username:
        print("Username cannot be empty.")
        sys.exit(1)

    password = getpass.getpass("Enter password: ").strip()
    if not password:
        print("Password cannot be empty.")
        sys.exit(1)

    # Hash the password
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    # Insert user
    con = sqlite3.connect(db)
    con.execute(
        "INSERT INTO users (username, password_hash, role, is_active, created_at) VALUES (?, ?, ?, ?, ?)",
        (username, password_hash, 'admin', 1, datetime.datetime.utcnow().isoformat() + 'Z')
    )
    con.commit()
    print(f"✅ User '{username}' created successfully.")

except sqlite3.IntegrityError:
    print(f"⚠️ User '{username}' already exists.")
except Exception as ex:
    print(f"❌ Error: {ex}")
finally:
    try:
        con.close()
    except Exception:
        pass
