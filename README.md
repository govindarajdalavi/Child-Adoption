# DDCAPMS - District Level Child Adoption Procedural Monitoring System

![DDCAPMS Banner](https://img.shields.io/badge/Status-Production--Ready-success?style=for-the-badge)
![Laws](https://img.shields.io/badge/Compliance-JJ_Act_2015_%7C_CARA_2022-blue?style=for-the-badge)

## 🏢 Overview
The **District Level Child Adoption Procedural Monitoring System (DDCAPMS)** is a professional, government-grade platform designed to modernize and digitize the adoption lifecycle for the Dharwad District. 

Built with a focus on legal compliance, accessibility, and transparency, this system ensures that every step of the adoption process—from child registration to final court decree—is monitored and recorded as per the **Juvenile Justice Act 2015** and **CARA Guidelines 2022**.

## ✨ Key Features
- **Multi-Role Dashboards**: Specialized interfaces for District Collector, Admin, CWC, Court, Orphanages, and Social Workers.
- **Legal Compliance Engine**: Automated tracking of the 15-stage adoption lifecycle, including mandatory 30-day notice periods and consent assessments.
- **Automated Document Generation**: One-click generation of Temporary Foster Care Orders and Final Adoption Decrees (PDF).
- **High-Contrast Design**: Premium, accessible UI with glassmorphism effects and role-based themes.
- **Real-time Notifications**: Instant updates for parents and officials on case status changes.

## 🛠️ Technology Stack
- **Backend**: Python / Flask
- **Database**: SQLite (SQLAlchemy ORM)
- **Frontend**: HTML5, CSS3 (Vanilla), JavaScript, Bootstrap 5
- **PDF Engine**: ReportLab
- **Animations**: AOS (Animate On Scroll)

## 🚀 Getting Started
1. **Clone the repo**:
   ```bash
   git clone https://github.com/govindarajdalavi/Child-Adoption.git
   ```
2. **Install dependencies**:
   ```bash
   pip install flask flask-sqlalchemy flask-login flask-bcrypt reportlab
   ```
3. **Run the application**:
   ```bash
   python app.py
   ```
4. **Seed Data**: Run `python sample_data.py` to populate the system with realistic government demo data.

## ⚖️ Legal Framework
This system implements:
- **JJ Act 2015 Section 36**: CWC investigation and Legally Free declaration.
- **JJ Act 2015 Section 58(3)**: Mandatory child consent assessment for children over 5 years.
- **CARA Regulation 8 & 13**: Home Study Reports and Post-Adoption Monitoring.

---
*Developed for the District Administration of Dharwad.*
