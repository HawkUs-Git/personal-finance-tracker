from fastapi import FastAPI, Request, Form, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import sqlite3
from typing import Optional
from datetime import datetime
import secrets
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=secrets.token_hex(16))
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def init_db():
    conn = sqlite3.connect("finance.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    date TEXT,
                    type TEXT,
                    category TEXT,
                    amount REAL
                )''')
    conn.commit()
    conn.close()

init_db()

async def get_current_user(request: Request) -> Optional[str]:
    return request.session.get("user")
@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})
@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    conn = sqlite3.connect("finance.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()
    if user:
        request.session["user"] = username
        return RedirectResponse(url="/dashboard", status_code=303)
    return RedirectResponse(url="/", status_code=303)
@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user: str = Depends(get_current_user)):
    if not user:
        return RedirectResponse(url="/", status_code=303)
    conn = sqlite3.connect("finance.db")
    c = conn.cursor()
    c.execute("SELECT * FROM transactions WHERE user_id=(SELECT id FROM users WHERE username=?) ORDER BY date DESC", (user,))
    transactions = c.fetchall()
    conn.close()
    return templates.TemplateResponse("dashboard.html", {"request": request, "transactions": transactions, "username": user})
@app.get("/add", response_class=HTMLResponse)
async def add_page(request: Request, user: str = Depends(get_current_user)):
    if not user:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("add_transaction.html", {"request": request})
@app.post("/add")
async def add_transaction(
    request: Request,
    date: str = Form(...),
    type: str = Form(...),
    category: str = Form(...),
    amount: float = Form(...),
    user: str = Depends(get_current_user)
):
    if not user:
        return RedirectResponse(url="/", status_code=303)
    conn = sqlite3.connect("finance.db")
    c = conn.cursor()
    c.execute("INSERT INTO transactions (user_id, date, type, category, amount) VALUES ((SELECT id FROM users WHERE username=?), ?, ?, ?, ?)",
              (user, date, type, category, amount))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/dashboard", status_code=303)



@app.get("/charts", response_class=HTMLResponse)
async def charts(request: Request, user: str = Depends(get_current_user)):
    if not user:
        return RedirectResponse(url="/", status_code=303)
    conn = sqlite3.connect("finance.db")
    c = conn.cursor()
    c.execute("SELECT category, SUM(amount) FROM transactions WHERE user_id=(SELECT id FROM users WHERE username=?) AND type='Expense' GROUP BY category", (user,))
    summary = c.fetchall()
    conn.close()
    labels = [row[0] for row in summary]
    values = [row[1] for row in summary]
    return templates.TemplateResponse("charts.html", {"request": request, "chart_data": {"labels": labels, "values": values}})