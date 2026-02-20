from fastapi import FastAPI,APIRouter,Depends, HTTPException, Header
from sqlalchemy import create_engine,Column,Integer,String,ForeignKey,DateTime, Boolean,Date,and_
from sqlalchemy.orm import sessionmaker,declarative_base,relationship,Session
from pydantic import BaseModel,EmailStr,field_validator
from typing import List,Optional,func
from datetime import date, datetime
import psycopg2

app = FastAPI(
    title ="Student Management API",
)
@app.get("/")
async def home():
    return {"message":"Student Management API - Dynamic Multi DB"}

MASTER_DB_URL = "postgresql://postgres:123456@localhost:5432/master_db"
master_engine = create_engine(MASTER_DB_URL)
MasterSessionLocal = sessionmaker(bind=master_engine, autoflush=False, autocommit=False)

Base = declarative_base()

STATIC_SUPER_ADMINS = [
    {"username": "nitya", "password": "1234"},
    {"username": "nityanand", "password": "5678"}
]






class College(Base):
    __tablename__ = "college"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    db_name = Column(String, unique=True)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)


class Student(Base):
    __tablename__ = "student"
    id = Column(Integer,primary_key=True,index=True)
    name= Column(String,nullable=False)
    email=Column(String,unique=True,nullable=False)
    phone=Column(Integer,nullable=False)
    college_id = Column(Integer, nullable=False)

    issued_books = relationship("IssuedBook", back_populates="student", cascade="all, delete-orphan")   

class Book(Base):
    __tablename__="book"
    id=Column(Integer,primary_key=True,index=True)
    title=Column(String,nullable=False)
    college_id = Column(Integer, nullable=False)
    created_by = Column(Integer, nullable=True)
    

    issued_books = relationship("IssuedBook", back_populates="book", cascade="all, delete-orphan")


class IssuedBook(Base):
    __tablename__ = "issued_book"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student.id"))
    book_id = Column(Integer, ForeignKey("book.id"))

    issue_date = Column(DateTime, default=datetime.utcnow)
    due_date = Column(Date, nullable=True)
    return_date = Column(DateTime, nullable=True)

    is_returned = Column(Boolean, default=False)
    fine_amount = Column(Integer, default=0)
    college_id = Column(Integer, nullable=False)

    student = relationship("Student", back_populates="issued_books", lazy="joined")
    book = relationship("Book", back_populates="issued_books", lazy="joined")
    
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    password = Column(String)
    role = Column(String)  # admin or librarian
    college_id = Column(Integer, nullable=False)
    
ROLE_STUDENT = "student"
ROLE_LIBRARIAN = "librarian"
ROLE_ADMIN = "admin"
ROLE_SUPER_ADMIN = "super_admin"



Base.metadata.create_all(bind=master_engine)


def create_college_database(db_name: str):
    conn = psycopg2.connect(
        dbname="postgres",
        user="postgres",
        password="123456",
        host="localhost",
        port="5432"
    )
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE {db_name}")
    cursor.close()
    conn.close()


def init_college_db(db_name: str):
    db_url = f"postgresql://postgres:123456@localhost:5432/{db_name}"
    engine = create_engine(db_url)
    Base.metadata.create_all(bind=engine)


def get_engine_by_college_id(college_id: int):
    db = MasterSessionLocal()
    college = db.query(College).filter(College.id == college_id).first()
    db.close()

    if not college:
        raise HTTPException(status_code=404, detail="College not found")

    db_url = f"postgresql://postgres:123456@localhost:5432/{college.db_name}"
    return create_engine(db_url)


def get_db(x_college_id: int = Header(...)):
    engine = get_engine_by_college_id(x_college_id)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



class CollegeCreate(BaseModel):
    name: str



class StudentBase(BaseModel):
    name:str
    email:EmailStr
    phone:int


    @field_validator('email')
    @classmethod
    def validate_email(cls,value):
        if not value.endswith("@gmail.com"):
            raise ValueError("email must end with @gmail.com")
        return value
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls,value):
        if len(str(value)) !=10:
            raise ValueError("phone number must be 10 digits")
        return value



class StudentCreate(StudentBase):
    pass
class StudentResponse(StudentCreate):
    id:int
    name:str
    email:EmailStr
    phone:int

    


    class Config:
        orm_mode=True

class BookBase(BaseModel):
    title:str

class BookCreate(BookBase):
    pass
class BookResponse(BookCreate):
    id:int

    class Config:
        orm_mode=True

class IssuedBookCreate(BaseModel):
    student_id: int
    book_id: int
    due_date: date


class IssuedBookResponse(BaseModel):
    id: int
    student_id: int
    book_id: int
    issue_date: datetime
    due_date: Optional[date]
    return_date: Optional[datetime]
    is_returned: bool
    fine_amount: int

    class Config:
        orm_mode=True


class UserCreate(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    role: str

    class Config:
        orm_mode = True

# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()










college_router = APIRouter(prefix="/college", tags=["college"])

@college_router.post("/")
def create_college(
    college: CollegeCreate,
    username: str = Header(...),
    password: str = Header(...)
):
    authenticate_super_admin(username, password)

    db = MasterSessionLocal()

    db_name = f"college_{college.name.lower().replace(' ', '_')}"

    existing = db.query(College).filter(College.name == college.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="College already exists")

    new_college = College(name=college.name, db_name=db_name)
    db.add(new_college)
    db.commit()
    db.refresh(new_college)

    create_college_database(db_name)
    init_college_db(db_name)

    db.close()

    return {"message": "College created successfully", "college_id": new_college.id}

@college_router.get("/")
def get_all_colleges(
    username: str = Header(...),
    password: str = Header(...)
):
    authenticate_super_admin(username, password)

    db = MasterSessionLocal()
    colleges = db.query(College).all()
    db.close()

    return [
        {
            "id": college.id,
            "name": college.name,
            "db_name": college.db_name,
            "status": college.status,
            "created_at": college.created_at
        }
        for college in colleges
    ]

app.include_router(college_router)


def authenticate_user(db: Session, username: str, password: str, college_id: int):
    user = db.query(User).filter(User.username == username, User.college_id == college_id).first()
    if not user or user.password != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return user


def authenticate_super_admin(username: str, password: str):
    for admin in STATIC_SUPER_ADMINS:
        if admin["username"] == username and admin["password"] == password:
            return {"username": username, "role": ROLE_SUPER_ADMIN}
    
    raise HTTPException(status_code=401, detail="Invalid super admin credentials")


def admin_required(db: Session, username: str, x_college_id: int):
    user = db.query(User).filter(
        User.username == username,
        User.college_id == x_college_id
    ).first()

    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    return user


def role_required(allowed_roles: list):
    def checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Allowed roles: {allowed_roles}"
            )
        return current_user
    return checker



auth_router = APIRouter(prefix="/auth", tags=["auth"])

@auth_router.post("/login")
def login(username: str, password: str, db: Session = Depends(get_db), x_college_id: int = Header(...)):
    user = authenticate_user(db, username, password, x_college_id)
    return {"message": "Login successful", "role": user.role}

# @auth_router.post("/signup")
# def signup(user: UserCreate, db: Session = Depends(get_db), x_college_id: int = Header(...)):
#     existing_user = db.query(User).filter(User.username == user.username).first()
#     if existing_user:
#         raise HTTPException(status_code=400, detail="Username already exists")



#     new_user = User(
#         username=user.username,
#         password=user.password,
#         role="student",  # Default role is student, can be changed to admin or librarian as needed
#         college_id=x_college_id
#     )

#     db.add(new_user)
#     db.commit()
#     db.refresh(new_user)
#     return {"message": "Student registered successfully"}


@auth_router.post("/signup")
def signup(user: UserCreate, db: Session = Depends(get_db), x_college_id: int = Header(...)):

    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = User(
        username=user.username,
        password=user.password,
        role=ROLE_STUDENT,  #  forced student role
        college_id=x_college_id
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "Student registered successfully"}

@auth_router.post("/create-admin")
def create_admin(
    username: str,
    password: str,
    college_id: int,
    super_admin_username: str = Header(...),
    super_admin_password: str = Header(...)
):
    authenticate_super_admin(super_admin_username, super_admin_password)

    engine = get_engine_by_college_id(college_id)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    old_admin = db.query(User).filter(User.role == ROLE_ADMIN,User.college_id == college_id).first()
    if old_admin:
        db.delete(old_admin)
        db.commit()

    admin = User(
        username=username,
        password=password,
        role=ROLE_ADMIN,
        college_id=college_id
    )

    db.add(admin)
    db.commit()
    db.close()

    return {"message": "College admin created/replaced successfully"}

def get_current_user(
    username: str = Header(...),
    password: str = Header(...),
    db: Session = Depends(get_db),
    x_college_id: int = Header(...)
):
    user = db.query(User).filter(
        User.username == username,
        User.password == password,  
        User.college_id == x_college_id
    ).first()

    if not user:
        raise HTTPException(status_code=401, detail="User not authenticated")

    return user



def get_admin_user(
    admin_username: str = Header(...),
    password: str = Header(...),
    db: Session = Depends(get_db),
    x_college_id: int = Header(...)
):
    user = authenticate_user(db, admin_username, password, x_college_id)

    if user.role != ROLE_ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")

    return user


def get_librarian_user(
    librarian_username: str = Header(...),
    password: str = Header(...),
    db: Session = Depends(get_db),
    x_college_id: int = Header(...)
):
    user = authenticate_user(db, librarian_username, password, x_college_id)

    if user.role != ROLE_LIBRARIAN:
        raise HTTPException(status_code=403, detail="Librarian access required")

    return user


def get_student_user(
    student_username: str = Header(...),
    password: str = Header(...),
    db: Session = Depends(get_db),
    x_college_id: int = Header(...)
):
    user = authenticate_user(db, student_username, password, x_college_id)

    if user.role != ROLE_STUDENT:
        raise HTTPException(status_code=403, detail="Student access required")

    return user

def get_admin_or_librarian_user(
    username: str = Header(...),
    password: str = Header(...),
    db: Session = Depends(get_db),
    x_college_id: int = Header(...)
):
    user = authenticate_user(db, username, password, x_college_id)

    if user.role not in [ROLE_ADMIN, ROLE_LIBRARIAN]:
        raise HTTPException(status_code=403, detail="Admin or Librarian required")

    return user



@auth_router.post("/create-librarian")
def create_librarian(
    user: UserCreate,
    db: Session = Depends(get_db),
    x_college_id: int = Header(...),
    current_user: User = Depends(get_admin_or_librarian_user)
):
    
    #  Only admin can create librarian
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can create librarian")

    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    librarian = User(
        username=user.username,
        password=user.password,
        role="librarian",
        college_id=x_college_id
    )

    db.add(librarian)
    db.commit()

    return {"message": "Librarian created successfully"}




@auth_router.get("/admins")
def get_all_admins(
    db: Session = Depends(get_db),
    x_college_id: int = Header(...),
    current_user: User = Depends(get_current_user)
):
    # Only admin can see admins
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can view admins")

    admins = db.query(User).filter(
        User.role == "admin",
        User.college_id == x_college_id
    ).all()

    return [
        {
            "id": admin.id,
            "username": admin.username,
            "role": admin.role,
            "college_id": admin.college_id
        }
        for admin in admins
    ]

app.include_router(auth_router)




student_router= APIRouter(prefix="/Student",tags=["student"])

@student_router.post("/")
def create_student(
    student: StudentCreate,
    db: Session = Depends(get_db),
    x_college_id: int = Header(...),
    current_user: User = Depends(get_admin_or_librarian_user)
):
    if current_user.role not in [ROLE_LIBRARIAN, ROLE_ADMIN]:
        raise HTTPException(status_code=403, detail="Only librarian or admin can create students")

    db_student = Student(**student.dict(), college_id=x_college_id)
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

@student_router.get("/", response_model=List[StudentResponse])
def get_all_student(
    db: Session = Depends(get_db),
    x_college_id: int = Header(...),
    current_user: User = Depends(get_admin_or_librarian_user)
):
    return db.query(Student).filter(Student.college_id == x_college_id).all()



@student_router.get("/{student_id}",response_model=StudentResponse)
def get_student_by_id(student_id:int,db:Session= Depends(get_db), x_college_id: int = Header(...)):
    student_obj=db.query(Student).filter(Student.id==student_id, Student.college_id == x_college_id).first()

    if not student_obj:
        raise HTTPException(status_code=404,detail="student not found")
    
    return student_obj

@student_router.put("/{student_id}",response_model=StudentResponse)
def update_student(student:StudentCreate,student_id:int,db:Session= Depends(get_db), x_college_id: int = Header(...)):
    student_obj=db.query(Student).filter(Student.id==student_id, Student.college_id == x_college_id).first()

    if not student_obj:
        raise HTTPException(status_code=404,detail="student not found")
    
    # student_obj.name=student.name
    # student_obj.email=student.email
    # student_obj.phone=student.phone


    for key ,value in student.dict().items():
        setattr(student_obj,key,value)



    db.commit()
    db.refresh(student_obj)
    return student_obj


@student_router.delete("/{student_id}")
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    x_college_id: int = Header(...),
    current_user: User = Depends(get_admin_user)
):
    student_obj = db.query(Student).filter(Student.id == student_id, Student.college_id == x_college_id).first()
    if not student_obj:
        raise HTTPException(status_code=404, detail="student not found")

    db.delete(student_obj)
    db.commit()

    return {"message": "student deleted successfully"}



app.include_router(student_router)



book_router= APIRouter(prefix="/Book",tags=["book"])



@book_router.post("/")
def create_book(
    book: BookCreate,
    db: Session = Depends(get_db),
    x_college_id: int = Header(...),
    current_user: User = Depends(get_admin_or_librarian_user)
):
    db_book=Book(**book.dict(), college_id=x_college_id, created_by=current_user.id)



    if current_user.role not in [ROLE_LIBRARIAN, ROLE_ADMIN]:
        raise HTTPException(status_code=403, detail="Only librarian or admin can create books")

    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book


@book_router.get("/",response_model=List[BookResponse])
def get_all_books(db:Session=Depends(get_db), x_college_id: int = Header(...)):
    return db.query(Book).filter(Book.college_id == x_college_id).all()


@book_router.get("/{book_id}",response_model=BookResponse)
def get_book_by_id(book_id:int,db:Session= Depends(get_db), x_college_id: int = Header(...)):
    book_obj=db.query(Book).filter(Book.id==book_id, Book.college_id == x_college_id).first()

    if not book_obj:
        raise HTTPException(status_code=404,detail="book not found")
    
    return book_obj


@book_router.put("/{book_id}",response_model=BookResponse)
def update_book(book:BookCreate,book_id:int,db:Session= Depends(get_db), x_college_id: int = Header(...)):
    book_obj=db.query(Book).filter(Book.id==book_id, Book.college_id == x_college_id).first()

    if not book_obj:
        raise HTTPException(status_code=404,detail="book not found")
    
    # book_obj.title=book.title
    # book_obj.student_id=book.student_id


    for key ,value in book.dict().items():
        setattr(book_obj,key,value)


    db.commit()
    db.refresh(book_obj)
    return book_obj


@book_router.delete("/{book_id}")
def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    x_college_id: int = Header(...),
    current_user: User = Depends(get_admin_user)
):
    book_obj = db.query(Book).filter(Book.id == book_id, Book.college_id == x_college_id).first()
    if not book_obj:
        raise HTTPException(status_code=404, detail="book not found")

    db.delete(book_obj)
    db.commit()

    return {"message": "Book deleted successfully"}



app.include_router(book_router)



issued_book_router= APIRouter(prefix="/IssuedBook",tags=["issued_book"])


@issued_book_router.post("/", response_model=IssuedBookResponse)
def issue_book(data: IssuedBookCreate, db: Session = Depends(get_db), x_college_id: int = Header(...), current_user: User = Depends(get_admin_or_librarian_user)):
    if current_user.role not in [ROLE_LIBRARIAN, ROLE_ADMIN]:
        raise HTTPException(status_code=403, detail="Only librarian or admin can issue books")

    student = db.query(Student).filter(Student.id == data.student_id, Student.college_id == x_college_id).first()
    book = db.query(Book).filter(Book.id == data.book_id, Book.college_id == x_college_id).first()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    existing = db.query(IssuedBook).filter(
        IssuedBook.student_id == data.student_id,
        IssuedBook.book_id == data.book_id,
        IssuedBook.is_returned == False
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Book already issued")

    issued = IssuedBook(
        student_id=data.student_id,
        book_id=data.book_id,
        due_date=data.due_date,
        college_id=x_college_id

    )

    db.add(issued)
    db.commit()
    db.refresh(issued)

    return issued


@issued_book_router.put("/{issue_id}/return", response_model=IssuedBookResponse)
def return_book(issue_id: int, db: Session = Depends(get_db), x_college_id: int = Header(...)):

    issued = db.query(IssuedBook).filter(IssuedBook.id == issue_id, IssuedBook.college_id == x_college_id).first()

    if not issued:
        raise HTTPException(status_code=404, detail="Issued book not found")

    issued.is_returned = True
    issued.return_date = datetime.utcnow()

   
    if issued.due_date and issued.return_date.date() > issued.due_date:
        days_late = (issued.return_date.date() - issued.due_date).days
        issued.fine_amount = days_late * 5  

    db.commit()
    db.refresh(issued)

    return issued

@issued_book_router.get("/delayed", response_model=list[IssuedBookResponse])
def get_delayed_books(db: Session = Depends(get_db), x_college_id: int = Header(...)):
    return db.query(IssuedBook).filter(
        IssuedBook.is_returned == False,
        IssuedBook.due_date < date.today(),
        IssuedBook.college_id == x_college_id
    ).all()



@issued_book_router.get("/", response_model=list[IssuedBookResponse])
def get_all_issued_books(db: Session = Depends(get_db), x_college_id: int = Header(...)):
    return db.query(IssuedBook).filter(IssuedBook.college_id == x_college_id).all()

app.include_router(issued_book_router)



dashboard_router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@dashboard_router.get("/")
def dashboard(db: Session = Depends(get_db), x_college_id: int = Header(...)):
    return {
        "total_students": db.query(Student).filter(Student.college_id == x_college_id).count(),
        "total_books": db.query(Book).filter(Book.college_id == x_college_id).count(),
        "issued_books": db.query(IssuedBook).filter(IssuedBook.is_returned == False, IssuedBook.college_id == x_college_id).count(),
    }

app.include_router(dashboard_router)

analytics_router = APIRouter(prefix="/analytics", tags=["analytics"])

@analytics_router.get("/student/{student_id}")
def student_analytics(
    student_id: int,
    db: Session = Depends(get_db),
    x_college_id: int = Header(...)
):
    student = db.query(Student).filter(
        Student.id == student_id,
        Student.college_id == x_college_id
    ).first()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    total_issued = db.query(IssuedBook).filter(
        IssuedBook.student_id == student_id,
        IssuedBook.college_id == x_college_id
    ).count()

    returned_late = db.query(IssuedBook).filter(
        IssuedBook.student_id == student_id,
        IssuedBook.is_returned == True,
        IssuedBook.fine_amount > 0,
        IssuedBook.college_id == x_college_id
    ).count()

    returned_on_time = db.query(IssuedBook).filter(
        IssuedBook.student_id == student_id,
        IssuedBook.is_returned == True,
        IssuedBook.fine_amount == 0,
        IssuedBook.college_id == x_college_id
    ).count()

    currently_issued = db.query(IssuedBook).filter(
        IssuedBook.student_id == student_id,
        IssuedBook.is_returned == False,
        IssuedBook.college_id == x_college_id
    ).count()

    total_fine = db.query(
        func.coalesce(func.sum(IssuedBook.fine_amount), 0)
    ).filter(
        IssuedBook.student_id == student_id,
        IssuedBook.college_id == x_college_id
    ).scalar()

    return {
        "student_id": student_id,
        "total_issued": total_issued,
        "returned_on_time": returned_on_time,
        "returned_late": returned_late,
        "currently_issued": currently_issued,
        "total_fine_paid": total_fine
    }

#Most Active Students (Top 5)
@analytics_router.get("/top-students")
def top_students(
    db: Session = Depends(get_db),
    x_college_id: int = Header(...)
):
    result = db.query(
        IssuedBook.student_id,
        func.count(IssuedBook.id).label("total_books")
    ).filter(
        IssuedBook.college_id == x_college_id
    ).group_by(
        IssuedBook.student_id
    ).order_by(
        func.count(IssuedBook.id).desc()
    ).limit(5).all()

    return result
#most issued books (Top 5)
@analytics_router.get("/top-books")
def top_books(
    db: Session = Depends(get_db),
    x_college_id: int = Header(...)
):
    result = db.query(
        IssuedBook.book_id,
        func.count(IssuedBook.id).label("issue_count")
    ).filter(
        IssuedBook.college_id == x_college_id
    ).group_by(
        IssuedBook.book_id
    ).order_by(
        func.count(IssuedBook.id).desc()
    ).limit(5).all()

    return result
#Monthly Fine Collection
@analytics_router.get("/monthly-fine")
def monthly_fine(
    db: Session = Depends(get_db),
    x_college_id: int = Header(...)
):
    result = db.query(
        func.date_trunc('month', IssuedBook.return_date).label("month"),
        func.sum(IssuedBook.fine_amount).label("total_fine")
    ).filter(
        IssuedBook.return_date != None,
        IssuedBook.college_id == x_college_id
    ).group_by(
        func.date_trunc('month', IssuedBook.return_date)
    ).all()

    return result

#top defaulters (students with highest fines)
@analytics_router.get("/top-defaulters")
def top_defaulters(
    db: Session = Depends(get_db),
    x_college_id: int = Header(...)
):
    result = db.query(
        IssuedBook.student_id,
        func.sum(IssuedBook.fine_amount).label("total_fine")
    ).filter(
        IssuedBook.college_id == x_college_id
    ).group_by(
        IssuedBook.student_id
    ).order_by(
        func.sum(IssuedBook.fine_amount).desc()
    ).limit(5).all()

    return result

app.include_router(analytics_router)