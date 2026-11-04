# Page to Voice - Backend API

Intelligent Audiobook Generation and Listening Platform API powered by FastAPI, SQLAlchemy, MySQL, and JWT Authentication.

## Setup & Running

1. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   Ensure `.env` exists with your MySQL credentials and JWT configuration.

3. **Initialize & Seed Database:**
   ```powershell
   python seed.py
   ```
   This creates tables and the default admin (`admin@pagetovoice.com` / `admin123`).

4. **Start Development Server:**
   ```powershell
   uvicorn main:app --reload --port 8000
   ```

5. **API Documentation:**
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`
