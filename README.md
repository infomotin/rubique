# 🧊 CubePermutation AI — MVC Group Theory Platform

**CubePermutation AI** is a production-grade web application built with a **Modular MVC (Model-View-Controller)** pattern, **MySQL database engine** (with auto-fallback), **OpenCV Computer Vision**, and **Kociemba Two-Phase Group Theory Algorithm**.

---

## 🌟 Architecture & Features

### 1. 🏛️ Modular MVC Pattern:
- **Models (`models/`)**:
  - [`models/db.py`](file:///d:/laragon/www/rubique/models/db.py): Dual-engine database connection layer (MySQL primary with automatic schema/database creation, SQLite automatic fallback).
  - [`models/user_model.py`](file:///d:/laragon/www/rubique/models/user_model.py): User authentication, profile updates, and secure password hashing.
  - [`models/solve_model.py`](file:///d:/laragon/www/rubique/models/solve_model.py): Speedcubing solve tracking, move counters, and statistical analytics.
- **Views (`templates/`)**:
  - [`templates/landing.html`](file:///d:/laragon/www/rubique/templates/landing.html): High-graphic mathematical landing page with 3D isometric teaser, group theory formula cards, and interactive intro.
  - [`templates/login.html`](file:///d:/laragon/www/rubique/templates/login.html): Separate secure sign-in page.
  - [`templates/register.html`](file:///d:/laragon/www/rubique/templates/register.html): Separate user registration page with validation.
  - [`templates/profile.html`](file:///d:/laragon/www/rubique/templates/profile.html): Dedicated user profile dashboard with total solves, best solution, average moves, and solve log.
  - [`templates/visualizer.html`](file:///d:/laragon/www/rubique/templates/visualizer.html): 3D isometric SVG cube, circular permutation orbit network, move ribbon, and playback deck.
- **Controllers (`controllers/`)**:
  - [`controllers/home_controller.py`](file:///d:/laragon/www/rubique/controllers/home_controller.py): Landing page controller (`/`).
  - [`controllers/auth_controller.py`](file:///d:/laragon/www/rubique/controllers/auth_controller.py): Authentication controller (`/login`, `/register`, `/logout`).
  - [`controllers/profile_controller.py`](file:///d:/laragon/www/rubique/controllers/profile_controller.py): Profile and analytics controller (`/profile`).
  - [`controllers/visualizer_controller.py`](file:///d:/laragon/www/rubique/controllers/visualizer_controller.py): Visualizer laboratory controller (`/visualizer`).
  - [`controllers/api_controller.py`](file:///d:/laragon/www/rubique/controllers/api_controller.py): REST API endpoints (`/api/scramble`, `/api/solve`, `/api/scan-image`, `/api/history`).

---

## 🗄️ MySQL Database Setup

The app connects automatically to MySQL in **Laragon / XAMPP / Localhost**:
- **Host**: `localhost`
- **Port**: `3306`
- **User**: `root`
- **Password**: *(configured in `config.py` or `.env`)*
- **Database**: `cube_permutation` *(created automatically on first launch)*

Tables created:
1. `users` — `id`, `username`, `email`, `password_hash`, `bio`, `avatar_color`, `created_at`
2. `solves` — `id`, `user_id`, `scramble`, `solution`, `move_count`, `created_at`

---

## 🚀 Live Access & Running Locally

### Live URL:
👉 **[http://127.0.0.1:5050](http://127.0.0.1:5050)**

### Start Server:
```bash
python app.py
```
