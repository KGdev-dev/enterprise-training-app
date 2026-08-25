# Deliverable 4: User Interface Design and Evaluation

## 4.1 Interface Design Wireframes (Text-Based Mock-Ups)

The interface utilizes a responsive, role-based architecture. Below are the structural wireframes for the four core workflows.

### 1. Learner Registration & Course Enrolment View

```text
+------------------------------------------------------------------------------------+
| [Logo] Enterprise Skills LMS               [👤 Learner Profile] [⚙️ Settings]      |
+------------------------------------------------------------------------------------+
| Course Enrolment Portal                                                            |
+------------------------------------------------------------------------------------+
| Select Course: [ Enterprise Python (C-PY) - 2 / 10 Seats Remaining  ▼ ]            |
| Full Name:     [ Ava Johnson                                         ]             |
| Email Address: [ ava.johnson@example.com                             ] [✓ Valid]   |
| ID / Passport: [ 9804125089087                                       ] [✓ Valid]   |
|                                                                                    |
| [ ] I agree to the academic integrity and prerequisite policies                    |
|                                                                                    |
|                     [ Clear Form ]    [ Submit Enrolment ]                         |
+------------------------------------------------------------------------------------+
```

### 2. Course Management Console (Administrator)
Plaintext

```
+------------------------------------------------------------------------------------+
| Course Inventory & Capacity Management                     [ + Add New Course ]    |
+---------+--------------------+----------+----------+----------+--------------------+
| Code    | Course Title       | Capacity | Enrolled | Status   | Actions            |
+---------+--------------------+----------+----------+----------+--------------------+
| C-PY    | Enterprise Python  |    25    |    24    | ACTIVE   | [Edit] [Close]     |
| C-ARC   | Cloud Architecture |    30    |    12    | ACTIVE   | [Edit] [Close]     |
| C-SEC   | Cyber Security     |    15    |    15    | FULL     | [Expand] [Reopen]  |
+---------+--------------------+----------+----------+----------+--------------------+
```

### 3. Support Ticket Creation (Learner / Admin)
Plaintext

```
+------------------------------------------------------------------------------------+
| Submit a Support Request                                                           |
+------------------------------------------------------------------------------------+
| Issue Category: [ Technical Support / LMS Outage                   ▼ ]             |
| Priority Level: [ HIGH - Blocking Assessment Submission            ▼ ]             |
| Description:                                                                       |
| +--------------------------------------------------------------------------------+ |
| | Unable to connect to the automated grading server during module assessment.    | |
| +--------------------------------------------------------------------------------+ |
| Attachment:     [ Browse Files... (max 5MB) ]                                      |
|                                                     [ Submit Ticket ]              |
+------------------------------------------------------------------------------------+
```

### 4. Operational & Performance Report Viewer (Administrator)

```text
+------------------------------------------------------------------------------------+
| Bugzot System Telemetry & Operational Analytics               [ Export CSV / PDF ] |
+------------------------------------------------------------------------------------+
| [ KPI METRICS ]                                                                    |
| Total Requests: 1,420 | Success Rate: 98.4% | Avg Latency: 12.4ms | Faults: 22     |
+------------------------------------------------------------------------------------+
| Filter By: Date [ Last 24 Hours ▼ ] | Severity [ ERROR & WARNING ▼ ]               |
|                                                                                    |
| Timestamp    | Category            | Details                          | Severity   |
| 10:14:02 UTC | CAPACITY_EXCEEDED   | Course C-SEC at max limit (15)   | WARNING    |
| 10:15:22 UTC | DUPLICATE_ATTEMPT   | Learner L101 already in C-PY     | WARNING    |
+------------------------------------------------------------------------------------+
```

## 4.2 Explanation of Design Decisions

- **Layout:** A modular, card-based layout ensures information is grouped logically. A persistent top navigation bar provides immediate access to profiles and settings.
- **Navigation:** Role-Based Access Control (RBAC) dictates navigation. Learners only see enrolment and support workflows, while Administrators have access to global course management and Bugzot telemetry. This reduces cognitive load.
- **Usability:** Action buttons (*Submit Enrolment*, *Submit Ticket*) are placed at the bottom right of forms, following natural eye-tracking patterns (F-pattern). High contrast ratios are used to meet accessibility standards.
- **Validation:** Forms utilize synchronous client-side validation (e.g., regex checking for email formatting) combined with visual indicators (`[✓ Valid]`). Real-time capacity indicators prevent users from attempting to enroll in full courses.

## 4.3 Evaluation of Proposed Design

- **Strengths:** The design offers high information density without visual clutter. The strict separation of roles ensures users only see what they need, while the real-time feedback (like capacity alerts) prevents operational errors before they reach the server.
- **Limitation:** Data-heavy administrative views, such as the Bugzot Operational Report and Course Inventory tables, do not scale well visually on smaller mobile screens. Columns may become cramped or require horizontal scrolling, leading to a poor mobile experience for administrators.
- **Recommended Improvement:** Implement a responsive table design that collapses into expandable "cards" or "accordions" when viewed on mobile devices. Additionally, introducing asynchronous server-side pagination for the Bugzot telemetry logs will prevent the browser from lagging when loading thousands of records.
