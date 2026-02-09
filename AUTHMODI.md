
STUDENT MANAGEMENT SYSTEM – AUTH & ROLE SECURITY UPGRADE PLAN

1. Problem Statement
Currently, any user can sign up as an admin by manually changing the role in the request.
This creates a serious security risk because students can delete books or perform admin actions.

2. Objectives
We will improve the authentication and authorization system to:
- Prevent users from choosing their role during signup.
- Automatically assign the role "student" to new users.
- Allow only one admin per college.
- Restrict admin-level operations (like deleting books) to admins only.
- Make role verification secure and reliable.

3. Planned Modifications

3.1 Remove Role from Signup Request
- Remove the 'role' field from the UserCreate model.
- Users will not be allowed to send role data from the client side.

3.2 Default Role Assignment
- During signup, the system will automatically assign role = "student".

3.3 Admin Creation Logic
- Create a special API endpoint for admin creation.
- Ensure only one admin exists per college.
- Prevent multiple admins from being created in the same college.

3.4 Secure Admin Validation
- Validate admin permissions by checking the database.
- Prevent role manipulation through request data.
- Ensure only admins can perform sensitive operations like deleting books.

3.5 Improve Delete Book API Security
- Modify the delete book API to verify admin privileges before deletion.
- Reject requests from non-admin users.

3.6 Future Enhancement (Optional)
- Implement JWT-based authentication.
- Store role and college_id in tokens.
- Use tokens to secure all APIs.

4. Expected Benefits
- Strong role-based access control.
- No unauthorized admin access.
- Secure multi-college system.
- Industry-level authentication design.

5. Implementation Strategy
- Step-by-step modification of auth router.
- Testing of role restrictions.
- Validation of admin-only operations.
- Optional upgrade to JWT authentication.

