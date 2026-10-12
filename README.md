# Flask & MySQL To-Do Application

A full-stack web application built with **Flask** and **MySQL**, featuring user authentication (registration/login) and a persistent task management (To-Do) system. Developed as part of database lab coursework.

---

## 🚀 Project Structure

```text
db-lab2/
├── database/
│   ├── schema.sql       # Structural database setup (CREATE DATABASE, TABLES)
│   └── lab2.sql         # Operational queries for data verification and testing
├── templates/
│   ├── login.html       # User login interface
│   ├── register.html    # User registration interface
│   └── todos.html       # To-Do management dashboard
├── .env                 # Environment variables / credentials (ignored by Git)
├── .env.example         # Template for environment variables
├── .gitignore           # Excludes venv/ and .env for security
├── app.py               # Main Flask application logic and database routes
└── README.md            # Project documentation