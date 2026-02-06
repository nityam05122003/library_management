Multi-College Library Management System (FastAPI + PostgreSQL)

⸻

1. System Overview

The Library Management System is a centralized FastAPI-based application designed to serve multiple colleges.
Each college acts as an independent tenant within the system.

The system ensures:
	•	Data isolation between colleges
	•	Role-based access control (RBAC)
	•	Secure authentication and authorization
	•	Scalability for multiple institutions
2. Architecture Overview

2.1 Architecture Type

The system follows a Multi-Tenant Architecture (Shared Database, Logical Isolation).

Client (College Users)
        ↓
     FastAPI Backend
        ↓
   Business Logic Layer
        ↓
     PostgreSQL Database



2.2 High-Level Flow

User Login → Authentication → Get college_id → 
All API requests filtered by college_id → 
CRUD operations → Response


3. Core Entities and Relationships

3.1 Entity Relationship Diagram (Logical)

College (1) ---- (M) Users
College (1) ---- (M) Students
College (1) ---- (M) Books
College (1) ---- (M) IssuedBooks

Student (1) ---- (M) IssuedBooks
Book (1) ---- (M) IssuedBooks

(M)  > multiple

4. Authentication & Authorization Flow

4.1 Login Flow (Technical)

1. User sends username + password
2. Backend validates credentials
3. System fetches user role + college_id
4. Backend returns token/session with college_id
5. All future requests include college_id


logic of authorisation
If user.role == "admin":
    Full access within college
Else if user.role == "librarian":
    Limited access within college
Else:
    Access denied




5. Data Isolation Strategy

5.1 Core Rule

Every query must include college_id.

Example (Student Fetch):

db.query(Student).filter(Student.college_id == college_id).all()


isolation flow

Request → Extract college_id → 
Filter database queries → 
Return college-specific data

This ensures:
	•	No cross-college data access
	•	No data clash
	•	Secure multi-tenant system


6. API Flow Design

6.1 Student Module Flow

Create Student → Assign college_id → Save to DB
Get Students → Filter by college_id → Return list
Update Student → Validate college_id → Update record
Delete Student → Validate college_id → Delete record

6.2 book module flow
Create Book → Assign college_id → Save to DB
Issue Book → Validate student + book + college_id
Return Book → Calculate fine → Update record

6.3 Issued Book Flow


Issue Book →
    Check student belongs to same college
    Check book belongs to same college
    Create issue record with college_id

Return Book →
    Update return_date
    Calculate fine if delayed


7.Role Management Flow

7.1 Role Scope

Roles are valid only within a college.

Example:
College A:
    admin, librarian
College B:
    admin, librarian

    Same role names can exist in different colleges without conflict.

8. System Workflow Diagram 

College Registration
        ↓
User Creation (Admin/Librarian)
        ↓
User Login
        ↓
college_id assigned to session/token
        ↓
User performs operations
        ↓
All data filtered by college_id
        ↓
Response returned

9. Technical Advantages
	•	Multi-tenant architecture
	•	Secure data isolation
	•	Scalable design
	•	Real-world SaaS pattern
	•	Easy to extend for future features


10. Conclusion

The proposed system architecture ensures that the Library Management System can support multiple colleges securely within a single application.
By introducing the College entity and enforcing college_id in all operations, the system achieves strong data isolation, scalability, and role-based security.

This technical design provides a robust foundation for building a real-world multi-college library management platform.





----------------------------------------------------------------------------------------------------------------------------
Technical Architecture & Multi-Tenant Flow Document

Tech Stack: FastAPI + PostgreSQL + SQLAlchemy 

⸻

1. System Definition (Enterprise Level)

The Multi-College Library Management System is a Multi-Tenant SaaS Application where:
	•	One application serves multiple colleges.
	•	Each college has multiple users.
	•	Each college’s data is fully isolated.
	•	Same roles and names can exist in different colleges.
	•	No cross-college data access is possible.

This system follows Tenant-Based Access Control + Role-Based Authorization + Logical/Physical Data Isolation.

⸻

2. Multi-Tenant Architecture Models 

 Model  — Separate Database per College

 PostgreSQL Server
 ├── college_A_db
 ├── college_B_db
 ├── college_C_db


 Each college has its own database.

 Pros:
	•	Maximum security
	•	No data clash possible
	•	Used in big SaaS... software as a service  systems
Cons:
	•	Complex management
	•	Dynamic DB routing needed



3. System Components (Technical View)

3.1 Core System Layers

Client Layer (College Users)
        ↓
API Gateway (FastAPI Routers)
        ↓
Authentication & Authorization Layer
        ↓
Tenant Resolution Layer (College Resolver)
        ↓
Business Logic Layer
        ↓
Database Routing Layer
        ↓
PostgreSQL Databases

4. Core Entities (Multi-College Design)

4.1 Main Tables (Logical Design)

College Table

college
- id
- name
- domain
- status
- created_at

users
- id
- username
- password_hash
- role (admin, librarian, user)
- college_id (FK)


student
- id
- name
- email
- phone
- college_id (FK)

book
- id
- title
- author
- college_id (FK)



issued_book
- id
- student_id
- book_id
- issue_date
- due_date
- return_date
- fine_amount
- college_id (FK)5. 
Multi-College Request Lifecycle 

5.1 Complete API Request Flow


Step 1: Client sends request (Login / API Call)
        ↓
Step 2: Authentication Service validates user
        ↓
Step 3: System extracts college_id from user record
        ↓
Step 4: Tenant Resolver identifies target college
        ↓
Step 5: Database Router selects correct database/schema
        ↓
Step 6: Business Logic executes query
        ↓
Step 7: Response returned to client

example
Request: GET /students

1. Token Validation
2. Extract user_id from token
3. Fetch user's college_id
4. Apply tenant filter or DB routing
5. Query only that college's students
6. Return response

6. Multi-Database Flow 
6.1 Database Routing Logic 

If college_id == 1 → connect to college_1_db
If college_id == 2 → connect to college_2_db
If college_id == 3 → connect to college_3_db

Multi-DB Architecture Diagram

FastAPI Application
        ↓
Tenant Resolver
        ↓
Dynamic DB Connection Manager
        ↓

│ college_A_db  │ college_B_db  │ college_C_db  │



. Tenant Isolation Strategy

7.1 Isolation Rules
	1.	User can access only their college data.
	2.	Every query must belong to one college.
	3.	Cross-college queries are blocked.
	4.	Roles are valid only inside a college.

⸻

7.2 Isolation Enforcement Points

Isolation is enforced at 3 levels:

1 Authentication Level
User → mapped to college_id.

2 Application Level
All APIs validate college_id.

3 Database Level
Separate DB or strict filtering.

⸻

8. Role-Based Access Control  in Multi-College System

8.1 Role Scope

Roles are scoped per college.

Example:

College A:
- admin
- librarian

College B:
- admin
- librarian

Same roles, different scope.

8.2 Authorization Flow

Request → Token → Role Check → College Check → Permission Granted

eg..
If user.role == "admin" AND user.college_id == resource.college_id:
    allow
Else:
    deny

    . Business Logic Flow (Technical)

9.1 Issue Book Flow


1. Validate user college
2. Validate student belongs to same college
3. Validate book belongs to same college
4. Check book availability
5. Create issued record in college DB

9.2 Return Book Flow

1. Validate issued record belongs to same college
2. Update return_date
3. Calculate fine
4. Update record



10. System Scalability Design

10.1 Horizontal Scalability
	•	Add more colleges without changing code.
	•	Add more databases dynamically.
11. Final Multi-College System Flow Diagram

College Registration
        ↓
Database Provisioning (per college)
        ↓
Admin Creation
        ↓
User Creation
        ↓
Login
        ↓
Tenant Identification (college_id)
        ↓
Database Routing
        ↓
CRUD Operations
        ↓
College-Specific Response