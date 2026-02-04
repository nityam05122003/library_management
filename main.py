from fastapi import FastAPI,APIRouter,Depends, HTTPException
from sqlalchemy import create_engine,Column,Integer,String,ForeignKey,DateTime, Boolean,Date,and_
from sqlalchemy.orm import sessionmaker,declarative_base,relationship,Session
from pydantic import BaseModel,EmailStr,field_validator
from typing import List,Optional
from datetime import date, datetime


app = FastAPI(
    title ="Student Management API",
)
@app.get("/")
async def home():
    return {"message":"this is student management api"}

DATABASE_URL="postgresql://postgres:123456@localhost:5432/studentdb"
Engine= create_engine(
    DATABASE_URL
)

SessionLocal= sessionmaker(
    bind = Engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

Base= declarative_base()


class Student(Base):
    __tablename__ = "student"
    id = Column(Integer,primary_key=True,index=True)
    name= Column(String,nullable=False)
    email=Column(String,unique=True,nullable=False)
    phone=Column(Integer,nullable=False)

    issued_books = relationship("IssuedBook", back_populates="student", cascade="all, delete-orphan")   

class Book(Base):
    __tablename__="book"
    id=Column(Integer,primary_key=True,index=True)
    title=Column(String,nullable=False)

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

    student = relationship("Student", back_populates="issued_books", lazy="joined")
    book = relationship("Book", back_populates="issued_books", lazy="joined")
    
Base.metadata.create_all(bind=Engine)

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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

student_router= APIRouter(prefix="/Student",tags=["student"])

@student_router.post("/",response_model=StudentResponse)
def create_student(student:StudentCreate,db:Session=Depends(get_db)):
    db_student=Student(**student.dict())
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

@student_router.get("/",response_model=List[StudentResponse])
def get_all_student(db:Session=Depends(get_db)):
    return db.query(Student).all()



@student_router.get("/{student_id}",response_model=StudentResponse)
def get_student_by_id(student_id:int,db:Session= Depends(get_db)):
    student_obj=db.query(Student).filter(Student.id==student_id).first()

    if not student_obj:
        raise HTTPException(status_code=404,detail="student not found")
    
    return student_obj

@student_router.put("/{student_id}",response_model=StudentResponse)
def update_student(student:StudentCreate,student_id:int,db:Session= Depends(get_db)):
    student_obj=db.query(Student).filter(Student.id==student_id).first()

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
def delete_student(student_id:int,db:Session= Depends(get_db)):
    student_obj=db.query(Student).filter(Student.id==student_id).first()
    if not student_obj:
        raise HTTPException(status_code=404,detail="student not found")
    
  
    db.delete(student_obj)
    db.commit()

    return {"message":"student deleted successfully"}



app.include_router(student_router)



book_router= APIRouter(prefix="/Book",tags=["book"])

@book_router.post("/",response_model=BookResponse)
def create_book(book:BookCreate,db:Session=Depends(get_db)):
    db_book=Book(**book.dict())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book


@book_router.get("/",response_model=List[BookResponse])
def get_all_books(db:Session=Depends(get_db)):
    return db.query(Book).all()


@book_router.get("/{book_id}",response_model=BookResponse)
def get_book_by_id(book_id:int,db:Session= Depends(get_db)):
    book_obj=db.query(Book).filter(Book.id==book_id).first()

    if not book_obj:
        raise HTTPException(status_code=404,detail="book not found")
    
    return book_obj


@book_router.put("/{book_id}",response_model=BookResponse)
def update_book(book:BookCreate,book_id:int,db:Session= Depends(get_db)):
    book_obj=db.query(Book).filter(Book.id==book_id).first()

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
def delete_book(book_id:int,db:Session= Depends(get_db)):
    book_obj=db.query(Book).filter(Book.id==book_id).first()
    if not book_obj:
        raise HTTPException(status_code=404,detail="book not found")

    db.delete(book_obj)
    db.commit()

    return {"message":"book deleted successfully"}


app.include_router(book_router)



issued_book_router= APIRouter(prefix="/IssuedBook",tags=["issued_book"])


@issued_book_router.post("/", response_model=IssuedBookResponse)
def issue_book(data: IssuedBookCreate, db: Session = Depends(get_db)):

    student = db.query(Student).filter(Student.id == data.student_id).first()
    book = db.query(Book).filter(Book.id == data.book_id).first()

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
def return_book(issue_id: int, db: Session = Depends(get_db)):

    issued = db.query(IssuedBook).filter(IssuedBook.id == issue_id).first()

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
def get_delayed_books(db: Session = Depends(get_db)):
    return db.query(IssuedBook).filter(
        IssuedBook.is_returned == False,
        IssuedBook.due_date < date.today()
    ).all()



@issued_book_router.get("/", response_model=list[IssuedBookResponse])
def get_all_issued_books(db: Session = Depends(get_db)):
    return db.query(IssuedBook).all()

app.include_router(issued_book_router)
