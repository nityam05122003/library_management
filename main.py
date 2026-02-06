from fastapi import FastAPI,APIRouter,Depends, HTTPException, Header
from sqlalchemy import create_engine,Column,Integer,String,ForeignKey,DateTime, Boolean,Date,and_
from sqlalchemy.orm import sessionmaker,declarative_base,relationship,Session
from pydantic import BaseModel,EmailStr,field_validator
from typing import List,Optional
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
    username = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String)  # admin or librarian
    college_id = Column(Integer, nullable=False)



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
    role: str 

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
def create_college(college: CollegeCreate):
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


app.include_router(college_router)


def authenticate_user(db: Session, username: str, password: str, college_id: int):
    user = db.query(User).filter(User.username == username, User.college_id == college_id).first()
    if not user or user.password != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return user



def admin_required(role: str):
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

student_router= APIRouter(prefix="/Student",tags=["student"])

@student_router.post("/",response_model=StudentResponse)
def create_student(student:StudentCreate,db:Session=Depends(get_db), x_college_id: int = Header(...)):
    db_student=Student(**student.dict(), college_id=x_college_id)
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

@student_router.get("/",response_model=List[StudentResponse])
def get_all_student(db:Session=Depends(get_db), x_college_id: int = Header(...)):
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
def delete_student(student_id:int,db:Session= Depends(get_db), x_college_id: int = Header(...)):
    student_obj=db.query(Student).filter(Student.id==student_id, Student.college_id == x_college_id).first()
    if not student_obj:
        raise HTTPException(status_code=404,detail="student not found")
    
  
    db.delete(student_obj)
    db.commit()

    return {"message":"student deleted successfully"}



app.include_router(student_router)



book_router= APIRouter(prefix="/Book",tags=["book"])

@book_router.post("/",response_model=BookResponse)
def create_book(book:BookCreate,db:Session=Depends(get_db), x_college_id: int = Header(...)):
    db_book=Book(**book.dict(), college_id=x_college_id)
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
def delete_book(book_id:int,db:Session= Depends(get_db), x_college_id: int = Header(...)):
    book_obj=db.query(Book).filter(Book.id==book_id, Book.college_id == x_college_id).first()
    if not book_obj:
        raise HTTPException(status_code=404,detail="book not found")

    db.delete(book_obj)
    db.commit()

    return {"message":"book deleted successfully"}


app.include_router(book_router)



issued_book_router= APIRouter(prefix="/IssuedBook",tags=["issued_book"])


@issued_book_router.post("/", response_model=IssuedBookResponse)
def issue_book(data: IssuedBookCreate, db: Session = Depends(get_db), x_college_id: int = Header(...)):

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
        due_date=data.due_date
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

auth_router = APIRouter(prefix="/auth", tags=["auth"])

@auth_router.post("/login")
def login(username: str, password: str, db: Session = Depends(get_db), x_college_id: int = Header(...)):
    user = authenticate_user(db, username, password, x_college_id)
    return {"message": "Login successful", "role": user.role}

@auth_router.post("/signup")
def signup(user: UserCreate, db: Session = Depends(get_db), x_college_id: int = Header(...)):
    new_user = User(**user.dict(), college_id=x_college_id)
    db.add(new_user)
    db.commit()
    return {"message": "User created"}

app.include_router(auth_router)



dashboard_router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@dashboard_router.get("/")
def dashboard(db: Session = Depends(get_db), x_college_id: int = Header(...)):
    return {
        "total_students": db.query(Student).count(),
        "total_books": db.query(Book).count(),
        "issued_books": db.query(IssuedBook).filter(IssuedBook.is_returned == False).count(),
    }

app.include_router(dashboard_router)
