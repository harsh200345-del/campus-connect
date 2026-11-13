import sqlite3
import os
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), 'campus_connect.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'student',
            course TEXT DEFAULT 'B.Tech',
            branch TEXT DEFAULT 'CSE',
            year TEXT DEFAULT '2nd Year',
            skills TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Notices Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            branch TEXT DEFAULT 'All',
            year TEXT DEFAULT 'All',
            priority TEXT DEFAULT 'Normal',
            attachment_link TEXT,
            deadline DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Opportunities Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS opportunities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            organization TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            eligibility_branch TEXT DEFAULT 'All',
            eligibility_year TEXT DEFAULT 'All',
            required_skills TEXT DEFAULT '',
            stipend_prize TEXT,
            apply_link TEXT,
            deadline DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Events Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            event_date DATE NOT NULL,
            time TEXT,
            venue TEXT,
            organizer TEXT,
            description TEXT,
            registration_link TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Bookmarks Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            opportunity_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, opportunity_id),
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (opportunity_id) REFERENCES opportunities (id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    conn.close()

def seed_sample_data():
    conn = get_db()
    cursor = conn.cursor()

    # Check if admin already exists
    cursor.execute("SELECT COUNT(*) FROM users WHERE email = 'admin@campusconnect.edu'")
    if cursor.fetchone()[0] == 0:
        admin_pass = generate_password_hash('admin123')
        cursor.execute('''
            INSERT INTO users (name, email, password, role, course, branch, year, skills)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('Head Admin', 'admin@campusconnect.edu', admin_pass, 'admin', 'Administration', 'All', 'Faculty', 'Management'))

    # Check if demo student exists
    cursor.execute("SELECT COUNT(*) FROM users WHERE email = 'student@campusconnect.edu'")
    if cursor.fetchone()[0] == 0:
        student_pass = generate_password_hash('student123')
        cursor.execute('''
            INSERT INTO users (name, email, password, role, course, branch, year, skills)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('Rahul Sharma', 'student@campusconnect.edu', student_pass, 'student', 'B.Tech', 'CSE', '2nd Year', 'Python, Web Development, SQL, Git'))

    # Check if demo 2nd student exists
    cursor.execute("SELECT COUNT(*) FROM users WHERE email = 'priya@campusconnect.edu'")
    if cursor.fetchone()[0] == 0:
        student2_pass = generate_password_hash('student123')
        cursor.execute('''
            INSERT INTO users (name, email, password, role, course, branch, year, skills)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('Priya Patel', 'priya@campusconnect.edu', student2_pass, 'student', 'B.Tech', 'ECE', '3rd Year', 'Embedded Systems, IoT, C++, Robotics'))

    # Check if notices exist
    cursor.execute("SELECT COUNT(*) FROM notices")
    if cursor.fetchone()[0] == 0:
        today = date.today()
        sample_notices = [
            (
                "🚨 Mandatory Mid-Semester Examination Schedule Announced",
                "The Even Semester Mid-Term Examinations will commence from next month. All students must ensure at least 75% attendance to obtain their hall tickets. Detailed timetable is available on the departmental notice board.",
                "Exam",
                "All",
                "All",
                "Urgent",
                "https://example.com/midsem-datesheet.pdf",
                (today + timedelta(days=5)).isoformat()
            ),
            (
                "CSE 2nd Year: Data Structures & Algorithms Assignment 3 Deadline",
                "Submit your Graph Algorithms implementation (Assignment 3) via the college portal before 11:59 PM. Late submissions will result in a 20% penalty. Check Git repository guidelines.",
                "Assignment",
                "CSE",
                "2nd Year",
                "High",
                "https://example.com/assignments/dsa3",
                (today + timedelta(days=2)).isoformat()
            ),
            (
                "Hostel Mess Committee Election & Rules Update",
                "Nominations are invited for Hostel Mess representative. Also, night curfew timings have been updated to 10:00 PM for all campus hostels. Discipline must be strictly maintained.",
                "Hostel",
                "All",
                "All",
                "Normal",
                "",
                (today + timedelta(days=10)).isoformat()
            ),
            (
                "TCS Campus Recruitment Training Program for 3rd & 4th Year",
                "Pre-placement training sessions for TCS Ninja and Digital profiles will start this Saturday in Audi 2. Mandatory for all registered 3rd & 4th year CSE & IT students.",
                "Placement",
                "CSE",
                "3rd Year",
                "High",
                "https://example.com/tcs-training",
                (today + timedelta(days=7)).isoformat()
            ),
            (
                "ECE Dept: Microprocessor Lab Schedule Revision",
                "Due to the upcoming technical symposium, the Microprocessor Lab for Batch A & B has been rescheduled to Thursday 2:00 PM - 5:00 PM.",
                "Academic",
                "ECE",
                "3rd Year",
                "Normal",
                "",
                (today + timedelta(days=4)).isoformat()
            )
        ]
        cursor.executemany('''
            INSERT INTO notices (title, description, category, branch, year, priority, attachment_link, deadline)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_notices)

    # Check if opportunities exist
    cursor.execute("SELECT COUNT(*) FROM opportunities")
    if cursor.fetchone()[0] == 0:
        today = date.today()
        sample_opps = [
            (
                "Smart India Hackathon (SIH) 2026 - College Internal Screening",
                "Ministry of Education & AICTE",
                "Nationwide initiative to provide students with a platform to solve pressing problems of society and government. Form teams of 6 (at least 1 female member). College will nominate top 10 teams.",
                "Hackathon",
                "All",
                "All",
                "Python, Web Development, AI/ML, App Development, Problem Solving",
                "₹1,00,000 Cash Prize per problem statement",
                "https://sih.gov.in",
                (today + timedelta(days=2)).isoformat()
            ),
            (
                "Google Summer of Code (GSoC) 2026 Mentorship",
                "Google Open Source",
                "A global online program that brings new contributors into open source software development. Work with mentors on a 12-week programming project.",
                "Internship",
                "CSE",
                "2nd Year",
                "Python, C++, Git, Open Source, Web Development",
                "$1,500 - $3,000 Stipend",
                "https://summerofcode.withgoogle.com",
                (today + timedelta(days=12)).isoformat()
            ),
            (
                "Full Stack Web Development Summer Internship",
                "InnovateTech Labs",
                "3-month remote internship working on modern web stacks (Flask/Django, React/Vue, PostgreSQL). Real client projects with high pre-placement offer (PPO) conversion.",
                "Internship",
                "CSE",
                "2nd Year",
                "Python, Web Development, SQL, JavaScript",
                "₹25,000 / month",
                "https://example.com/apply-innovatetech",
                (today + timedelta(days=4)).isoformat()
            ),
            (
                "National Robotics & Embedded IoT Challenge",
                "IIT Bombay Techfest",
                "Build autonomous rovers and IoT smart telemetry systems. Hardware kit grants provided to shortlisted teams.",
                "Competition",
                "ECE",
                "3rd Year",
                "Embedded Systems, IoT, C++, Robotics, Arduino",
                "₹75,000 Prize Pool",
                "https://example.com/robotics-challenge",
                (today + timedelta(days=8)).isoformat()
            ),
            (
                "Reliance Foundation Undergraduate Scholarship 2026",
                "Reliance Foundation",
                "Merit-cum-means scholarship supporting exceptional undergraduate students throughout their degree program. Open for all engineering disciplines with family income criteria.",
                "Scholarship",
                "All",
                "1st Year",
                "Academic Excellence, Problem Solving",
                "Up to ₹2,00,000 grant",
                "https://www.reliancefoundation.org",
                (today + timedelta(days=18)).isoformat()
            ),
            (
                "AWS Cloud & DevOps Hands-on Bootcamp",
                "AWS Student Club",
                "2-day hands-on intensive workshop covering Docker, CI/CD pipelines, and AWS EC2/S3 deployment. Certificate of completion from AWS Academy.",
                "Workshop",
                "CSE",
                "All",
                "Cloud, Python, Linux, DevOps",
                "Free AWS Credits ($100)",
                "https://example.com/aws-workshop",
                (today + timedelta(days=3)).isoformat()
            ),
            (
                "TCS CodeVita Season 13 - Global Coding Contest",
                "Tata Consultancy Services",
                "The world's largest competitive programming competition recognized by Guinness World Records. Top performers get direct interview calls for TCS Digital & Prime roles.",
                "Competition",
                "All",
                "3rd Year",
                "Python, C++, Java, Data Structures, Algorithms",
                "Top Tier Placement + $20,000 prizes",
                "https://tcscodevita.com",
                (today + timedelta(days=15)).isoformat()
            )
        ]
        cursor.executemany('''
            INSERT INTO opportunities (title, organization, description, category, eligibility_branch, eligibility_year, required_skills, stipend_prize, apply_link, deadline)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_opps)

    # Check if events exist
    cursor.execute("SELECT COUNT(*) FROM events")
    if cursor.fetchone()[0] == 0:
        today = date.today()
        sample_events = [
            (
                "Invento 2026: Annual Inter-College Technical Fest",
                "Fest",
                (today + timedelta(days=14)).isoformat(),
                "09:30 AM - 06:00 PM",
                "Main College Auditorium & Labs",
                "Student Technical Council",
                "3 days of coding marathons, robotics battles, esports, paper presentations, and celebrity guest lectures. Cash prizes over ₹3 Lakhs!",
                "https://example.com/invento2026"
            ),
            (
                "AI in Healthcare: Expert Guest Lecture by Dr. K. Verma",
                "Seminar",
                (today + timedelta(days=6)).isoformat(),
                "11:00 AM - 01:00 PM",
                "Seminar Hall 1",
                "Department of Computer Science & Engineering",
                "Interactive session on Computer Vision and Deep Learning applications in modern medical diagnostics. E-certificates for all attendees.",
                "https://example.com/ai-seminar"
            ),
            (
                "Campus Coding Club (C3) Annual Recruitment Drive",
                "Club",
                (today + timedelta(days=3)).isoformat(),
                "04:00 PM - 06:00 PM",
                "Computer Lab 4",
                "Campus Coding Club",
                "Looking for passionate developers, designers, and event managers to join the core team. Coding and interview round on site.",
                "https://example.com/c3-recruitment"
            )
        ]
        cursor.executemany('''
            INSERT INTO events (title, category, event_date, time, venue, organizer, description, registration_link)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_events)

    conn.commit()
    conn.close()
