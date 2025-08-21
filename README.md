# Smart Adaptive AAC MVP

## Overview
This project is a **Smart Adaptive AAC (Augmentative and Alternative Communication) system** designed for children. It features AI-driven adaptive input, emotion detection, and eye tracking, with a gamified referral system for parents. This MVP provides a fully functional platform for immediate testing and usage.

Key features:
- Dual Input: **Touch / Sensor Screen** or **Eye Tracking**
- AI Auto-Selection of Best Input
- Real-Time Emotion Detection
- Continuous AI Learning
- Parent Control & Blocking System
- Referral-Based Plan Upgrades (Gamified)

## Tech Stack
- **Backend:** Python, Flask
- **Frontend:** HTML, CSS, JavaScript
- **AI Models:** Ollama Llama 3.2 for adaptive communication
- **Computer Vision:** OpenCV, MediaPipe
- **Database:** SQLite (or SQLAlchemy for ORM)
- **Environment:** Python 3.11, venv

## Features

### 1. Input Options
- Sensor-based selection via touchscreen, buttons, or switches.
- Eye-tracking-based selection using webcam and gaze detection.
- AI dynamically chooses the most efficient input method for the child.

### 2. Emotion & Contextual Adaptation
- AI analyzes the child’s facial expressions in real time.
- Detects emotions like sad, angry, frustrated, or tired.
- Adjusts layout, speed, and voice output accordingly.

### 3. Learning & Control
- AI continuously learns and adapts predictions, vocabulary, and layouts.
- Parents can restrict words, lock settings, and control features.

### 4. Referral System
- Parents can refer others.
- Referral rewards upgrade the plan automatically (Basic → Plus → Pro → Max).

### 5. User Interface
- Simple symbol-based board with buttons.
- Webcam video feed overlay for emotion and eye tracking.
- Parent dashboard with settings and referral tracking.

## Installation

### 1. Clone the repository

git clone https://github.com/aviv555m/echoes/tree/main/aac_mvp_v2_eye_emotion

cd aac_mvp_v2_eye_emotion


