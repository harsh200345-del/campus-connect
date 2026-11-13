# 🎓 CampusConnect — Smart College Information & Opportunity Hub

> **A personalized, centralized college platform combining a Smart Notice Board and a College Opportunity Hub with branch, year, and skill-based recommendation algorithms.**

Developed for **B.Tech / MCA / BCA Mini Project Submission**.

---

## 🌟 Key Highlights & Problem Solved

### The Problem
In almost every college, academic notices, exam timetables, hackathons, internships, and workshops are scattered across dozens of unorganized WhatsApp groups, Telegram channels, bulletin boards, and official websites. Students frequently miss critical deadlines (like SIH registration, exam form submissions, or scholarship grants) or get overwhelmed by irrelevant notices meant for other branches.

### The Solution: CampusConnect
1. **Targeted Notice Board:** Students only see notices relevant to their **Branch** and **Year** (e.g., CSE 2nd Year notices don't clutter Mechanical students' feed).
2. **Personalized Opportunity Hub:** Uses a **Rule- & Skill-Based Recommendation Engine** to score and rank hackathons, internships, competitions, scholarships, and workshops matching the student's exact skill set (e.g., Python + Web Dev).
3. **Deadline Radar:** Dynamic urgency badges (e.g., `⚠️ Closes in 2 days`) alert students before applications close.
4. **Full College Admin Panel:** Faculty/Admins can broadcast notices, target specific cohorts, curate opportunities with skill tags, and track student registrations.

---

## 🏗️ Architecture & Modules

### 1. Student Portal
- **Secure Authentication:** Register with Course, Branch, Year, and Technical Skills.
- **Personalized Dashboard:** Displays highest-match opportunities, urgent deadlines, targeted notices, and campus events.
- **Bookmark / Save:** One-click save to track opportunities of interest.
- **Live Profile Editor:** Modifying skills dynamically recalculates and re-ranks opportunity scores instantly!

### 2. Smart Notice Board
- Filter by category: **Exams**, **Assignments**, **Academic**, **Placements**, **Hostel**, **Emergency**.
- Toggle between **"My Department"** and **"All College Notices"**.
- Download official attachments/links.

### 3. College Opportunity Hub
- Filter by: **Hackathons**, **Internships**, **Competitions**, **Scholarships**, **Workshops**, **Placements**, **Certifications**.
- Match Score pill (e.g. `🔥 95% Match`) showing specifically which skills matched.
- Direct links to official external application portals (e.g., SIH, GSoC, Unstop).

### 4. Campus Calendar & Events
- Upcoming inter-college technical fests, workshops, guest lectures, and club recruitment drives.

### 5. Admin Control Panel
- **Notice Management:** Publish notices with branch/year targeting, priority (Urgent/High/Normal), and deadlines.
- **Opportunity Curating:** Add opportunities with required skills tags, stipend/prizes, eligibility criteria.
- **Campus Event Scheduling:** Add seminars and technical fests with dates and venues.
- **Student Roster:** View all registered students and their technical skill distribution.

---

## 🚀 How to Run the Project Locally

### 1. Open Terminal / PowerShell
Navigate to the project directory:
```bash
cd "C:\Users\Harsh mani pandey\OneDrive\Desktop\CampusConnect"
```

### 2. Run the Application
```bash
python app.py
```
*(The database `campus_connect.db` is initialized and pre-seeded automatically on first run!)*

### 3. Open in Browser
Visit: **`http://127.0.0.1:5000`**

---

## 🔑 Demo Login Credentials

For quick evaluation and viva demonstrations, pre-seeded accounts are provided:

| Role | Email | Password | Details |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@campusconnect.edu` | `admin123` | Full access to publish notices, opportunities, events |
| **Student** | `student@campusconnect.edu` | `student123` | Rahul Sharma (B.Tech CSE 2nd Year, Python + Web Dev) |
| **Student 2**| `priya@campusconnect.edu` | `student123` | Priya Patel (B.Tech ECE 3rd Year, Embedded + IoT) |

*(You can also register a brand new student account with custom skills!)*

---

## 🧠 Recommendation Algorithm Explanation (Viva Ready)

**Formula:**
$$\text{Score} = \text{Branch Score (30)} + \text{Year Score (20)} + \text{Skills Overlap Score (50)}$$

1. **Branch Match (30 pts):** If opportunity is open to `All` or equals student's branch $\rightarrow$ 30 pts.
2. **Year Match (20 pts):** If opportunity is open to `All` or equals student's year $\rightarrow$ 20 pts.
3. **Skills Match (50 pts):**
   $$\text{Skill Overlap Ratio} = \frac{|\text{Student Skills} \cap \text{Required Skills}|}{|\text{Required Skills}|}$$
   $$\text{Skills Score} = \text{Skill Overlap Ratio} \times 50$$
4. Total score is bounded between $10\%$ and $100\%$ and sorted in descending order.

---

## 🎯 Frequently Asked Viva Questions (FAQ)

1. **Q: Why use SQLite instead of MySQL?**
   - *A: SQLite is serverless, zero-configuration, and ACID-compliant, making it ideal for demonstration and local development. The database schema uses standard SQL, allowing immediate migration to MySQL/PostgreSQL by simply altering the connection string.*
2. **Q: How does the system prevent notification fatigue?**
   - *A: By default, the student notice board filters notices using `WHERE (branch = 'All' OR branch = ?) AND (year = 'All' OR year = ?)`, completely removing irrelevant departmental clutter.*
3. **Q: How are passwords stored securely?**
   - *A: Passwords are encrypted using Werkzeug's salted cryptographic hash (`generate_password_hash` with pbkdf2:sha256).*
4. **Q: Can this scale to an entire university?**
   - *A: Yes, with a PostgreSQL/MySQL database backend and deployment on Gunicorn/Nginx or cloud services like AWS EC2 / Render.*
