import sqlite3
from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'tvojestrasne_tajny_klic'  # Pro práci se session / uživateli

DATABASE = 'databaze.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Pro přístup k sloupcům přes název
    return conn
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS visited_castles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            castle_id INTEGER NOT NULL,
            visited_at TEXT,
            rating INTEGER DEFAULT 0,
            note TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (castle_id) REFERENCES pamatky (id)
        )
    ''')

    # Pojistka pro doplnění sloupců, pokud tabulka již existovala
    try:
        cursor.execute("ALTER TABLE visited_castles ADD COLUMN visited_at TEXT")
    except Exception:
        pass
    try:
        cursor.execute(
            "ALTER TABLE visited_castles ADD COLUMN rating INTEGER DEFAULT 0"
        )
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE visited_castles ADD COLUMN note TEXT")
    except Exception:
        pass

    conn.commit()
    conn.close()


# Zavolej tuto funkci hned při startu aplikace (před app.run)
init_db()
# Inicializace tabulky navštívených hradů (pokud ještě neexistuje)
def init_visited_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS visited_castles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            castle_id INTEGER NOT NULL,
            visited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (castle_id) REFERENCES hrady (id),
            UNIQUE(user_id, castle_id)
        );
    ''')
    conn.commit()
    conn.close()

# Zavoláme při startu aplikace
init_visited_db()


@app.route('/')
def index():
    return render_template('index.html')


# --- API ENDPOINTY ---
@app.route('/api/castles', methods=['GET'])
def get_castles():
    user_id = session.get('user_id')

    conn = get_db_connection()
    cursor = conn.cursor()

    if user_id:
        cursor.execute(
            '''
            SELECT p.*, 
                   CASE WHEN v.castle_id IS NOT NULL THEN 1 ELSE 0 END as is_visited,
                   v.visited_at, v.rating, v.note
            FROM pamatky p
            LEFT JOIN visited_castles v ON p.id = v.castle_id AND v.user_id = ?
        ''',
            (user_id,),
        )
    else:
        cursor.execute(
            'SELECT p.*, 0 as is_visited, NULL as visited_at, 0 as rating, NULL as note FROM pamatky p'
        )

    castles = cursor.fetchall()
    conn.close()

    result = [dict(row) for row in castles]
    return jsonify(result)

@app.route('/api/user/visited', methods=['GET'])
def get_user_visited():
    if 'user_id' not in session:
        return jsonify({'error': 'Nejste přihlášeni'}), 401

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        '''
        SELECT p.id, p.nazev, p.typ, p.kraj, p.lat, p.lon, p.foto,
               v.visited_at, v.rating, v.note
        FROM pamatky p
        JOIN visited_castles v ON p.id = v.castle_id
        WHERE v.user_id = ?
        ORDER BY v.visited_at DESC, p.nazev ASC
    ''',
        (session['user_id'],),
    )

    visited = cursor.fetchall()
    conn.close()

    result = []
    for row in visited:
        result.append({
            'id': row['id'],
            'nazev': row['nazev'],
            'typ': row['typ'],
            'kraj': row['kraj'],
            'lat': row['lat'],
            'lon': row['lon'],
            'foto': row['foto'],
            'visited_at': row['visited_at'],
            'rating': row['rating'],
            'note': row['note'],
        })

    return jsonify(result)
# --- AUTENTIZACE ENDPOINTY ---

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Chybí uživatelské jméno nebo heslo'}), 400

    conn = get_db_connection()
    # Zkontrolujeme, zda uživatel již neexistuje
    user = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
    if user:
        conn.close()
        return jsonify({'error': 'Uživatel s tímto jménem již existuje'}), 400

    hashed_password = generate_password_hash(password)
    conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Registrace byla úspěšná! Nyní se můžete přihlásit.'})


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()

    if user and check_password_hash(user['password'], password):
        session['user_id'] = user['id']
        session['username'] = user['username']
        return jsonify({'success': True, 'username': user['username']})
    
    return jsonify({'error': 'Nesprávné uživatelské jméno nebo heslo'}), 401


@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})


@app.route('/api/user-status', methods=['GET'])
def user_status():
    if 'user_id' in session:
        return jsonify({'logged_in': True, 'username': session.get('username')})
    return jsonify({'logged_in': False})

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Spočítáme ulovené památky pro každého uživatele a seřadíme od největšího po nejmenší
    cursor.execute('''
        SELECT u.username, COUNT(v.castle_id) as count
        FROM users u
        LEFT JOIN visited_castles v ON u.id = v.user_id
        GROUP BY u.id
        ORDER BY count DESC, u.username ASC
        LIMIT 20
    ''')

    rows = cursor.fetchall()
    conn.close()

    leaderboard = [{'username': row['username'], 'count': row['count']} for row in rows]
    return jsonify(leaderboard)
@app.route('/api/castle/<int:castle_id>/visit', methods=['POST'])
def toggle_visit(castle_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Nejste přihlášeni'}), 401

    user_id = session['user_id']
    data = request.get_json() or {}

    visited_at = data.get('visited_at')
    rating = data.get('rating', 0)
    note = data.get('note', '')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        'SELECT id FROM visited_castles WHERE user_id = ? AND castle_id = ?',
        (user_id, castle_id),
    )
    existing = cursor.fetchone()

    if existing:
        # Pokud už záznam existuje a posíláme akci 'delete', odebereme ho
        if data.get('action') == 'delete':
            cursor.execute(
                'DELETE FROM visited_castles WHERE user_id = ? AND castle_id = ?',
                (user_id, castle_id),
            )
            message = 'Památka odebrána z ulovených.'
            visited = False
        else:
            # Jinak aktualizujeme poznámku, hodnocení a datum
            cursor.execute(
                '''
                UPDATE visited_castles 
                SET visited_at = ?, rating = ?, note = ?
                WHERE user_id = ? AND castle_id = ?
            ''',
                (visited_at, rating, note, user_id, castle_id),
            )
            message = 'Úlovek aktualizován!'
            visited = True
    else:
        # Vložení nového úlovku
        cursor.execute(
            '''
            INSERT INTO visited_castles (user_id, castle_id, visited_at, rating, note)
            VALUES (?, ?, ?, ?, ?)
        ''',
            (user_id, castle_id, visited_at, rating, note),
        )
        message = 'Památka ulovena!'
        visited = True

    conn.commit()
    conn.close()
    return jsonify({'message': message, 'visited': visited})


if __name__ == '__main__':
    app.run(debug=True)