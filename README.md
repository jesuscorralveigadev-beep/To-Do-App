# To-Do-App
A modern desktop To-Do application built with Python, CustomTkinter, and SQLite.
The project focuses on clean UI/UX design inspired by the Frutiger Aero aesthetic,
while implementing a complete task management system with persistent storage.

This application was designed as a portfolio project to demonstrate both
software engineering fundamentals and user interface design.

---

## Features

- Create, edit, delete, and complete tasks
- Persistent storage using SQLite
- Priority system with visual color indicators
- Due dates and task metadata
- Search and filter tasks in real time
- Light and Dark mode with full UI theming
- Smooth UI interactions and visual feedback
- Task details panel for editing
- Export tasks to CSV
- Desktop-ready executable (.exe)

---

## Tech Stack

- **Python**
- **CustomTkinter** (modern Tkinter-based UI framework)
- **SQLite** (local persistent database)
- **PyInstaller** (application packaging)

---

## Installation (Development)

### 1. Clone the repository
  git clone https://github.com/jesuscorralveigadev-beep/To-Do-App
  cd To-Do-App
  
### 2. Create virtual environment (recommended)
  python -m venv\Scripts\activate
  
### 3. Install dependencies
  pip install customtkinter
  
### 4. Run the application
  python To-Do-App.py

---

## Packaging as .exe (PyInstaller)

### 1. Install PyInstaller
  pip install pyinstaller

### 2. Build executable
  pyinstaller --onefile --windowed --icon=todo_portfolio_assets/app_icon.ico To-Do-App.py

### 3. Output
  The executable will be created in: dist/To-Do-App.exe

You can distribute this file without requiring Python to be installed.

---

## Design Philosophy

This project emphasizes:
- Clear visual hierarchy
- Readable typography
- Soft gradients and glass-like panels
- Minimalist but expressive UI
- Visual feedback for user actions

The Frutiger Aero aesthetic was chosen to explore expressive UI design
while maintaining usability and clarity.

---

## What This Project Demonstrates

- Desktop application development with Python
- GUI design and layout management
- SQLite database modeling and CRUD operations
- State management and UI synchronization
- Theming and dynamic style updates
- Clean, maintainable code structure
- End-to-end project completion

---

## Screenshots

<img width="1679" height="1049" alt="ScreenShoot" src="https://github.com/user-attachments/assets/34df8579-ee1b-42f1-8035-5decba2dfeec" />

---

## License

This project is for educational and portfolio purposes.
