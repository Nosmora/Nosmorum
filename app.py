from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Création de la table "messages"
def create_table():
    conn = sqlite3.connect('forum.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  content TEXT,
                  parent_id INTEGER,
                  created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

# Fonction pour créer une connexion à la base de données
def get_db():
    conn = sqlite3.connect('forum.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_messages_for_thread(thread_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM messages WHERE id = ? OR parent_id = ? ORDER BY created_at', (thread_id, thread_id))
    messages = [dict(row) for row in c.fetchall()]
    conn.close()
    return messages

def send_reply_to_thread(thread_id, message):
    conn = get_db()
    c = conn.cursor()
    c.execute('INSERT INTO messages (content, parent_id) VALUES (?, ?)', (message, thread_id))
    conn.commit()
    conn.close()

@app.route('/')
def index():
    # Récupération des messages racines
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM messages WHERE parent_id IS NULL ORDER BY created_at DESC')
    messages = [dict(row) for row in c.fetchall()]
    conn.close()
    return render_template('index.html', messages=messages)

@app.route('/thread/<int:thread_id>')
def view_thread(thread_id):
    messages = get_messages_for_thread(thread_id)
    return render_template('view_thread.html', messages=messages, thread_id=thread_id)

@app.route('/thread/<int:thread_id>/reply', methods=['POST'])
def reply(thread_id):
    message = request.form['message']
    send_reply_to_thread(thread_id, message)
    return redirect(url_for('view_thread', thread_id=thread_id))

@app.route('/message/<int:message_id>')
def message(message_id):
    # Récupération du message et de ses réponses
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM messages WHERE id = ?', (message_id,))
    message = c.fetchone()
    c.execute('SELECT * FROM messages WHERE parent_id = ? ORDER BY created_at', (message_id,))
    replies = [dict(row) for row in c.fetchall()]
    conn.close()
    return render_template('message.html', message=message, replies=replies)

@app.route('/creer-message', methods=['GET', 'POST'])
def create_message():
    if request.method == 'POST':
        content = request.form['contenu']
        parent_id = request.form.get('parent_id')
        conn = get_db()
        c = conn.cursor()
        if not parent_id:
            # Création d'un nouveau message racine
            c.execute('INSERT INTO messages (content) VALUES (?)', (content,))
        else:
            # Création d'une réponse
            c.execute('INSERT INTO messages (content, parent_id) VALUES (?, ?)', (content, parent_id))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    return render_template('nouveau-message.html')

if __name__ == '__main__':
    create_table()
    app.run(debug=True)

