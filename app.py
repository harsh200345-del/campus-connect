import os
from functools import wraps
from datetime import datetime, date
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db, init_db, seed_sample_data
from recommendation import rank_opportunities_for_student, get_deadline_status

app = Flask(__name__)
app.secret_key = 'campusconnect_super_secret_key_btech_miniproject_2026'

# Custom template filters
@app.template_filter('deadline_badge')
def deadline_badge_filter(deadline_str):
    return get_deadline_status(deadline_str)

# Login decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Admin authentication required.', 'warning')
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash('Access restricted to administrators.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Context processor for global user data
@app.context_processor
def inject_user():
    user = None
    if 'user_id' in session:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
        row = cursor.fetchone()
        conn.close()
        if row:
            user = dict(row)
    return dict(current_user=user)

# ----------------- PUBLIC ROUTES ----------------- #

@app.route('/')
def index():
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM notices")
    notices_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM opportunities")
    opps_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'student'")
    students_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM events")
    events_count = cursor.fetchone()[0]

    # Sample featured notices & opportunities for landing preview
    cursor.execute("SELECT * FROM notices ORDER BY id DESC LIMIT 3")
    recent_notices = [dict(row) for row in cursor.fetchall()]
    cursor.execute("SELECT * FROM opportunities ORDER BY id DESC LIMIT 3")
    featured_opps = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return render_template('index.html', 
                           notices_count=notices_count,
                           opps_count=opps_count,
                           students_count=students_count,
                           events_count=events_count,
                           recent_notices=recent_notices,
                           featured_opps=featured_opps)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard') if session.get('role') != 'admin' else url_for('admin_dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['role'] = user['role']
            session['branch'] = user['branch']
            session['year'] = user['year']
            
            flash(f"Welcome back, {user['name']}!", 'success')
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email address or password. Please try again.', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        course = request.form.get('course', 'B.Tech').strip()
        branch = request.form.get('branch', 'CSE').strip()
        year = request.form.get('year', '2nd Year').strip()
        skills = request.form.get('skills', '').strip()

        if not name or not email or not password:
            flash('All primary fields are required.', 'warning')
            return render_template('register.html')

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE LOWER(email) = ?", (email,))
        if cursor.fetchone():
            conn.close()
            flash('Email is already registered. Please log in.', 'danger')
            return render_template('register.html')

        hashed_pw = generate_password_hash(password)
        cursor.execute('''
            INSERT INTO users (name, email, password, role, course, branch, year, skills)
            VALUES (?, ?, ?, 'student', ?, ?, ?, ?)
        ''', (name, email, hashed_pw, course, branch, year, skills))
        conn.commit()
        
        # Log user in directly
        new_id = cursor.lastrowid
        conn.close()

        session['user_id'] = new_id
        session['user_name'] = name
        session['role'] = 'student'
        session['branch'] = branch
        session['year'] = year

        flash('Registration successful! Welcome to CampusConnect.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

# ----------------- STUDENT PORTAL ----------------- #

@app.route('/dashboard')
@login_required
def dashboard():
    if session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))

    conn = get_db()
    cursor = conn.cursor()

    # Get student record
    cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    student = dict(cursor.fetchone())

    # Get notices relevant to branch and year or 'All'
    cursor.execute('''
        SELECT * FROM notices 
        WHERE (branch = 'All' OR branch = ?)
          AND (year = 'All' OR year = ?)
        ORDER BY 
            CASE priority 
                WHEN 'Urgent' THEN 1 
                WHEN 'High' THEN 2 
                ELSE 3 
            END, id DESC 
        LIMIT 6
    ''', (student['branch'], student['year']))
    relevant_notices = [dict(row) for row in cursor.fetchall()]

    # Emergency announcement banner (if any)
    cursor.execute('''
        SELECT * FROM notices 
        WHERE priority = 'Urgent' 
        ORDER BY id DESC LIMIT 1
    ''')
    urgent_banner = cursor.fetchone()
    urgent_banner = dict(urgent_banner) if urgent_banner else None

    # Get all active opportunities for recommendation
    cursor.execute("SELECT * FROM opportunities")
    all_opps = [dict(row) for row in cursor.fetchall()]

    # Run recommendation algorithm
    ranked_opps = rank_opportunities_for_student(student, all_opps)

    # Get user bookmarks
    cursor.execute("SELECT opportunity_id FROM bookmarks WHERE user_id = ?", (session['user_id'],))
    bookmarked_ids = set(row[0] for row in cursor.fetchall())

    # Annotate opportunities with bookmark status
    for opp in ranked_opps:
        opp['is_bookmarked'] = opp['id'] in bookmarked_ids

    # Top recommended opportunities (top 4)
    top_recommended = ranked_opps[:4]

    # Deadline alerts: Opportunities ending within 3 days
    urgent_deadlines = [
        opp for opp in ranked_opps 
        if 0 <= opp['deadline_info']['days'] <= 3
    ]

    # Upcoming events (next 3)
    cursor.execute("SELECT * FROM events ORDER BY event_date ASC LIMIT 3")
    upcoming_events = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return render_template(
        'dashboard.html',
        student=student,
        notices=relevant_notices,
        urgent_banner=urgent_banner,
        top_recommended=top_recommended,
        urgent_deadlines=urgent_deadlines,
        upcoming_events=upcoming_events,
        bookmarked_count=len(bookmarked_ids)
    )

@app.route('/notices')
@login_required
def notices():
    category = request.args.get('category', 'all')
    scope = request.args.get('scope', 'my') # 'my' or 'all'
    search = request.args.get('search', '').strip().lower()

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    student = dict(cursor.fetchone())

    query = "SELECT * FROM notices WHERE 1=1"
    params = []

    if scope == 'my' and student['role'] == 'student':
        query += " AND (branch = 'All' OR branch = ?) AND (year = 'All' OR year = ?)"
        params.extend([student['branch'], student['year']])

    if category != 'all':
        query += " AND category = ?"
        params.append(category)

    if search:
        query += " AND (LOWER(title) LIKE ? OR LOWER(description) LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    query += " ORDER BY CASE priority WHEN 'Urgent' THEN 1 WHEN 'High' THEN 2 ELSE 3 END, id DESC"
    cursor.execute(query, params)
    notices_list = [dict(row) for row in cursor.fetchall()]

    # Annotate deadline
    for n in notices_list:
        n['deadline_info'] = get_deadline_status(n['deadline'])

    conn.close()
    return render_template('notices.html', notices=notices_list, current_category=category, current_scope=scope, search_query=search, student=student)

@app.route('/opportunities')
@login_required
def opportunities():
    category = request.args.get('category', 'all')
    search = request.args.get('search', '').strip().lower()

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    student = dict(cursor.fetchone())

    query = "SELECT * FROM opportunities WHERE 1=1"
    params = []

    if category != 'all':
        query += " AND category = ?"
        params.append(category)

    if search:
        query += " AND (LOWER(title) LIKE ? OR LOWER(description) LIKE ? OR LOWER(required_skills) LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

    cursor.execute(query, params)
    raw_opps = [dict(row) for row in cursor.fetchall()]

    # Personalized ranking
    ranked_opps = rank_opportunities_for_student(student, raw_opps)

    # Bookmarks
    cursor.execute("SELECT opportunity_id FROM bookmarks WHERE user_id = ?", (session['user_id'],))
    bookmarked_ids = set(row[0] for row in cursor.fetchall())
    for opp in ranked_opps:
        opp['is_bookmarked'] = opp['id'] in bookmarked_ids

    conn.close()

    return render_template('opportunities.html', opportunities=ranked_opps, current_category=category, search_query=search, student=student)

@app.route('/bookmarks')
@login_required
def bookmarks():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    student = dict(cursor.fetchone())

    cursor.execute('''
        SELECT o.* FROM opportunities o
        JOIN bookmarks b ON o.id = b.opportunity_id
        WHERE b.user_id = ?
        ORDER BY b.created_at DESC
    ''', (session['user_id'],))
    bookmarked_opps = [dict(row) for row in cursor.fetchall()]

    ranked_opps = rank_opportunities_for_student(student, bookmarked_opps)
    for opp in ranked_opps:
        opp['is_bookmarked'] = True

    conn.close()
    return render_template('bookmarks.html', opportunities=ranked_opps, student=student)

@app.route('/bookmark/toggle/<int:opp_id>', methods=['POST'])
@login_required
def toggle_bookmark(opp_id):
    conn = get_db()
    cursor = conn.cursor()
    user_id = session['user_id']

    cursor.execute("SELECT id FROM bookmarks WHERE user_id = ? AND opportunity_id = ?", (user_id, opp_id))
    existing = cursor.fetchone()

    if existing:
        cursor.execute("DELETE FROM bookmarks WHERE id = ?", (existing[0],))
        conn.commit()
        bookmarked = False
        message = "Removed from bookmarks."
    else:
        cursor.execute("INSERT INTO bookmarks (user_id, opportunity_id) VALUES (?, ?)", (user_id, opp_id))
        conn.commit()
        bookmarked = True
        message = "Saved to bookmarks!"

    conn.close()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({'success': True, 'bookmarked': bookmarked, 'message': message})
    
    flash(message, 'info')
    return redirect(request.referrer or url_for('opportunities'))

@app.route('/events')
@login_required
def events():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events ORDER BY event_date ASC")
    events_list = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return render_template('events.html', events=events_list)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        course = request.form.get('course', 'B.Tech').strip()
        branch = request.form.get('branch', 'CSE').strip()
        year = request.form.get('year', '2nd Year').strip()
        skills = request.form.get('skills', '').strip()

        cursor.execute('''
            UPDATE users
            SET name = ?, course = ?, branch = ?, year = ?, skills = ?
            WHERE id = ?
        ''', (name, course, branch, year, skills, session['user_id']))
        conn.commit()

        session['user_name'] = name
        session['branch'] = branch
        session['year'] = year

        flash('Your profile and recommendation preferences have been updated!', 'success')
        return redirect(url_for('profile'))

    cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    student = dict(cursor.fetchone())
    conn.close()

    return render_template('profile.html', student=student)

# ----------------- ADMIN PANEL ----------------- #

@app.route('/admin')
@admin_required
def admin_dashboard():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM notices")
    total_notices = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM opportunities")
    total_opps = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM events")
    total_events = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'student'")
    total_students = cursor.fetchone()[0]

    cursor.execute("SELECT * FROM notices ORDER BY id DESC LIMIT 5")
    recent_notices = [dict(row) for row in cursor.fetchall()]

    cursor.execute("SELECT * FROM opportunities ORDER BY id DESC LIMIT 5")
    recent_opps = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return render_template(
        'admin_dashboard.html',
        total_notices=total_notices,
        total_opps=total_opps,
        total_events=total_events,
        total_students=total_students,
        recent_notices=recent_notices,
        recent_opps=recent_opps
    )

# --- Admin Notices Management --- #
@app.route('/admin/notices')
@admin_required
def admin_notices():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notices ORDER BY id DESC")
    notices_list = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return render_template('admin_notices.html', notices=notices_list)

@app.route('/admin/notices/add', methods=['POST'])
@admin_required
def admin_add_notice():
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    category = request.form.get('category', 'General')
    branch = request.form.get('branch', 'All')
    year = request.form.get('year', 'All')
    priority = request.form.get('priority', 'Normal')
    attachment_link = request.form.get('attachment_link', '').strip()
    deadline = request.form.get('deadline', None)

    if not deadline:
        deadline = None

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO notices (title, description, category, branch, year, priority, attachment_link, deadline)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (title, description, category, branch, year, priority, attachment_link, deadline))
    conn.commit()
    conn.close()

    flash('Notice broadcasted successfully!', 'success')
    return redirect(url_for('admin_notices'))

@app.route('/admin/notices/delete/<int:id>', methods=['POST'])
@admin_required
def admin_delete_notice(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notices WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    flash('Notice deleted successfully.', 'info')
    return redirect(url_for('admin_notices'))

# --- Admin Opportunities Management --- #
@app.route('/admin/opportunities')
@admin_required
def admin_opportunities():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM opportunities ORDER BY id DESC")
    opps_list = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return render_template('admin_opportunities.html', opportunities=opps_list)

@app.route('/admin/opportunities/add', methods=['POST'])
@admin_required
def admin_add_opportunity():
    title = request.form.get('title', '').strip()
    organization = request.form.get('organization', '').strip()
    description = request.form.get('description', '').strip()
    category = request.form.get('category', 'Internship')
    eligibility_branch = request.form.get('eligibility_branch', 'All')
    eligibility_year = request.form.get('eligibility_year', 'All')
    required_skills = request.form.get('required_skills', '').strip()
    stipend_prize = request.form.get('stipend_prize', '').strip()
    apply_link = request.form.get('apply_link', '').strip()
    deadline = request.form.get('deadline', None)

    if not deadline:
        deadline = None

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO opportunities 
        (title, organization, description, category, eligibility_branch, eligibility_year, required_skills, stipend_prize, apply_link, deadline)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (title, organization, description, category, eligibility_branch, eligibility_year, required_skills, stipend_prize, apply_link, deadline))
    conn.commit()
    conn.close()

    flash('Opportunity posted successfully!', 'success')
    return redirect(url_for('admin_opportunities'))

@app.route('/admin/opportunities/delete/<int:id>', methods=['POST'])
@admin_required
def admin_delete_opportunity(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM opportunities WHERE id = ?", (id,))
    cursor.execute("DELETE FROM bookmarks WHERE opportunity_id = ?", (id,))
    conn.commit()
    conn.close()

    flash('Opportunity deleted successfully.', 'info')
    return redirect(url_for('admin_opportunities'))

# --- Admin Events Management --- #
@app.route('/admin/events')
@admin_required
def admin_events():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events ORDER BY event_date ASC")
    events_list = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return render_template('admin_events.html', events=events_list)

@app.route('/admin/events/add', methods=['POST'])
@admin_required
def admin_add_event():
    title = request.form.get('title', '').strip()
    category = request.form.get('category', 'Fest')
    event_date = request.form.get('event_date')
    time = request.form.get('time', '').strip()
    venue = request.form.get('venue', '').strip()
    organizer = request.form.get('organizer', '').strip()
    description = request.form.get('description', '').strip()
    registration_link = request.form.get('registration_link', '').strip()

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO events (title, category, event_date, time, venue, organizer, description, registration_link)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (title, category, event_date, time, venue, organizer, description, registration_link))
    conn.commit()
    conn.close()

    flash('Event added successfully!', 'success')
    return redirect(url_for('admin_events'))

@app.route('/admin/events/delete/<int:id>', methods=['POST'])
@admin_required
def admin_delete_event(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM events WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    flash('Event deleted successfully.', 'info')
    return redirect(url_for('admin_events'))

# --- Admin Students Directory --- #
@app.route('/admin/students')
@admin_required
def admin_students():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, course, branch, year, skills, created_at FROM users WHERE role = 'student' ORDER BY id DESC")
    students_list = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return render_template('admin_students.html', students=students_list)

if __name__ == '__main__':
    # Initialize and seed database if not exists
    init_db()
    seed_sample_data()
    print("=" * 60)
    print("🚀 CampusConnect Server is starting...")
    print("🌐 Open your browser at: http://127.0.0.1:5000")
    print("🔑 Default Admin Credentials: admin@campusconnect.edu | admin123")
    print("🎓 Default Student Credentials: student@campusconnect.edu | student123")
    print("=" * 60)
    app.run(debug=True, host='127.0.0.1', port=5000)
