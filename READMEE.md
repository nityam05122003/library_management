Multi-College & Multi-User Data Isolation Design Document

⸻

1. Introduction

This document describes the design of a single Library Management Application that is used by multiple colleges, where each college has multiple users such as admin, librarian, and staff. The primary objective of this system is to ensure complete data isolation and security, so that:
	•	Users of one college cannot access data of another college.
	•	Data does not clash between colleges, even if names, roles, or records are similar.
	•	Roles are assigned independently inside each college.
	•	The application remains scalable, secure, and maintainable.

This architecture follows the concept of a Multi-College (Multi-Tenant) System.

⸻

2. System Overview

The application is a single centralized system shared by multiple colleges.
Each college acts as an independent entity within the system.

Key Characteristics:
	•	One application → Many colleges
	•	One college → Many users
	•	Strict separation of data between colleges
	•	Role-based access control inside each college

⸻

3. Multi-College Architecture Concept

In this system, every record is associated with a specific college using a unique identifier called college_id.

All major entities such as:
	•	Users
	•	Students
	•	Books
	•	Issued Books
	•	Reports

are linked to a particular college.

 Data Isolation Strategy

4.1 College-Based Data Segregation

Every table in the database contains a college_id field.
This ensures that data is always filtered based on the college.

Example Principle:
	•	A user from College A can only access records where college_id = College A.
	•	A user from College B can only access records where college_id = College B.

This prevents:
	•	Data leakage between colleges
	•	Data conflicts due to similar names or roles
	•	Unauthorized access

⸻

4.2 Handling Similar Names and Roles

Since multiple colleges may have:
	•	Students with the same name
	•	Books with the same title
	•	Users with the same role (admin, librarian)
	•	Emails or usernames that look similar

the system avoids conflicts by linking every record with college_id.

Thus:
	•	Same student name in different colleges → Allowed
	•	Same role in different colleges → Allowed
	•	Same book title in different colleges → Allowed

But data remains completely separate.

⸻

5. Role Management Inside Each College

Each college has its own role hierarchy.

Roles Defined:

1. Admin (College-Level)
Responsibilities:
	•	Manage users inside the college
	•	Assign roles (admin, librarian, staff)
	•	Manage books and students
	•	View reports of their college
	•	Full control within their college only

2. Librarian
Responsibilities:
	•	Issue books
	•	Return books
	•	Manage student records
	•	Calculate fines
	•	Cannot access other colleges’ data

3. Staff/User
Responsibilities:
	•	View limited data
	•	Perform basic operations as permitted
	•	No administrative privileges

Important Rule:

Roles are not global, they are college-specific.

Example:
	•	Admin of College A ≠ Admin of College B
	•	Librarian of College A ≠ Librarian of College C

⸻

6. Security Mechanisms

6.1 Authentication

Each user logs in using credentials that are linked to a specific college.

6.2 Authorization

After login:
	•	The system identifies the user’s college.
	•	All API requests are filtered by the user’s college.
	•	Role-based permissions are applied.

6.3 Access Control Rules

















No user can:
	•	Access data of another college
	•	Modify records of another college
	•	View reports of another college

⸻

7. Prevention of Data Clash

To prevent data clashes, the system ensures:
	1.	Every record has college_id.
	2.	Queries are always filtered by college_id.
	3.	Primary keys are global, but logical separation is maintained by college_id.
	4.	Business rules are applied per college.

Example:

Even if two colleges have:
	•	Student name: Rahul
	•	Book title: Database Systems
	•	Role: Librarian

Their data will never mix because they belong to different colleges.

⸻

8. Scalability and Future Possibilities

The system is designed to support:
	•	Unlimited colleges
	•	Unlimited users per college
	•	Independent role management per college
	•	Future integration with authentication systems (JWT, OAuth)
	•	Advanced reporting per college

⸻

9. Conclusion

This Library Management System is designed as a secure, scalable, and multi-college application.
By using college-based data isolation and role-based access control, the system ensures that:
	•	Each college operates independently within a single application.
	•	Data privacy and security are maintained.
	•	Similar names, roles, and records do not cause conflicts.
	•	Users can only access their own college data.

This architecture makes the system suitable for real-world deployment across multiple educational institutions while maintaining strict data security and organizational boundaries.




College → Users → Students → Books → IssuedBooks