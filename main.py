#uvicorn main:app --reload
from fastapi import FastAPI
from database import engine
import models
from fastapi.staticfiles import StaticFiles


models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app = FastAPI(title="Expense Tracker API")
@app.get("/")
def root():
    return {"message": "hello"}



from routers import users, transactions, categories
app.include_router(categories.router)
app.include_router(users.router)
app.include_router(transactions.router)

app.mount("/static", StaticFiles(directory="static"), name="static")