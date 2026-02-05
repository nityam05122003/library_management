
LIBRARY MANAGEMENT SYSTEM
TECHNICAL PROJECT DOCUMENTATION

1. INTRODUCTION
The Library Management System (LMS) is a backend application developed using FastAPI and PostgreSQL to manage students, books, and issued books in a library environment. The system supports role-based access control, data isolation, book issuing, returning, fine calculation, and multi-user operations.

2. OBJECTIVES
- Automate library operations.
- Provide secure multi-user access.
- Implement role-based authorization.
- Maintain accurate records of students and books.
- Track book issuance, returns, and fines.
- Ensure data privacy between multiple users.

3. SYSTEM OVERVIEW
The system is built using:
- Backend Framework: FastAPI
- Database: PostgreSQL
- ORM: SQLAlchemy
- Validation: Pydantic
- API Documentation: Swagger (OpenAPI)

Architecture: RESTful API-based layered architecture.

4. USER ROLES
4.1 Admin
- Manage users (create librarian/user).
- Full access to books, students, issued books.
- View reports and analytics.

4.2 Librarian
- Add/update/delete books.
- Issue and return books.
- View issued books and delayed books.

4.3 User (Library Member)
- Register student records.
- View own issued books.
- Cannot view other users' data.

5. MULTI-USER DATA ISOLATION
Each record is associated with an owner (user_id). Users can only access their own data. Admin can access all data.

6. DATABASE DESIGN
Entities:
- Student
- Book
- IssuedBook
- User

Relationships:
- One Student → Many IssuedBooks
- One Book → Many IssuedBooks
- One User → Many Students/Books/IssuedBooks

7. DATABASE TABLE STRUCTURE

Student Table:
- id (PK)
- name
- email
- phone

Book Table:
- id (PK)
- title

IssuedBook Table:
- id (PK)
- student_id (FK)
- book_id (FK)
- issue_date
- due_date
- return_date
- is_returned
- fine_amount

User Table:
- id (PK)
- username
- password
- role

8. API MODULES

8.1 Student Module
- Create student
- Get all students
- Get student by ID
- Update student
- Delete student

8.2 Book Module
- Create book
- Get all books
- Get book by ID
- Update book
- Delete book

8.3 Issued Book Module
- Issue book
- Return book
- Get issued books
- Get delayed books

8.4 Authentication Module
- Login
- Role validation

9. BUSINESS LOGIC

9.1 Book Issuing Logic
- Validate student and book existence.
- Prevent duplicate issue.
- Save issue record.

9.2 Book Return Logic
- Mark book as returned.
- Calculate fine.
- Update record.

9.3 Fine Calculation
Fine = (Return Date - Due Date) × Rate per day.

10. SECURITY FEATURES
- Role-based access control.
- Input validation.
- Data isolation.
- Secure authentication.

11. ERROR HANDLING
- 404: Resource not found.
- 400: Invalid request.
- 401: Unauthorized access.
- 500: Internal server error.

12. WORKFLOW DIAGRAM (LOGICAL FLOW)
User → API → Validation → Database → Response

13. FUTURE ENHANCEMENTS
- JWT Authentication
- Password hashing
- Frontend UI (React/Angular)
- Notification system
- Book availability tracking
- Multi-library support
- Cloud deployment

14. ADVANTAGES
- Fast performance
- Secure architecture
- Scalable design
- Modular structure

15. LIMITATIONS
- No frontend UI currently
- Basic authentication
- Manual role assignment

16. CONCLUSION
The Library Management System provides a scalable and secure solution for managing library operations with modern backend technologies. The system can be extended to enterprise-level applications with further enhancements.

