# 🏨 Hotel Management System

A simple yet functional Hotel Management System built using **Flask**, **Pandas**, and **Docx**. It provides a web-based interface to manage hotel rooms, customer records, transactions, and generate daily reports.

---

## ✅ Features

- **Room Management**
- **Room Shift Feature**
- **Transaction Management**
- **Report Generation**
- **Discord Webhook Alerts**
- **Discord Bot Commands**
- **Analysis**
- **Role-Based User Authentication**
- **Event Log**

---

## ⚙️ Installation Instructions

### Requirements

- Python 3.8+
- Flask  
- Pandas  
- python-docx  
- flask-cors  
- backports.zoneinfo *(for Python < 3.9)*

---

### How to Run

Clone the repository:
```bash
git clone https://github.com/PS218909/Hotel-Management-System
```
Navigate to the project directory:
```bash
cd Hotel-Management-System
```
Install dependencies:
```bash
pip install -r requirements.txt
```
Update src/config.py (To utilize all the function): 
```python
HOTEL_NAME = "Hotel Name"
HOTEL_ADDRESS = "Hotel Address"
....
TESTING_CHANNEL_ID = 0 
UPDATE_CHANNEL_ID = 0  
DISCORD_BOT_TOKEN = "BOT TOKEN"

```
Start the application:
```bash
python main.py
```
---

## 🚀 Future Improvements
-  Replace CSV with SQLite
-  Add more operations
-  Improve UI