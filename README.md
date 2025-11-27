# 💰 FinanzApp - Personal Finance Management System

Full-stack web application for personal finance management with automated biweekly projections, alert system, and analytical dashboard.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)
![SQLite](https://img.shields.io/badge/SQLite-3-orange.svg)

## 🚀 Key Features

### 📊 Smart Biweekly Projection
- Automated projections up to 12 months ahead
- Visual traffic light system (🟢 Green, 🟡 Yellow, 🔴 Red)
- Precise calculations considering custom payment dates
- Trend analysis and minimum projected balance

### 💳 Credit Card Management
- Support for multiple credit cards
- Distinction between regular expenses and installment payments (Interest-Free Months)
- Automatic tracking of monthly payments
- Upcoming due date alerts

### 📈 Analytical Dashboard
- Interactive charts with Chart.js
- Historical income vs expenses analysis
- Expense distribution by category
- Visual projection of future balance

### 🎯 Purchase Simulator
- Financial impact projection before purchasing
- Comparison with/without purchase
- Automatic recommendations based on projected balance

## 🛠️ Technologies Used

**Backend:**
- Python 3.9+
- Flask 3.0
- SQLite
- python-dateutil

**Frontend:**
- HTML5 / CSS3
- JavaScript (ES6+)
- Chart.js
- Responsive design

## 📦 Installation

```bash
# Clone repository
git clone https://github.com/your-username/finanzapp.git
cd finanzapp

# Install dependencies
pip install flask python-dateutil

# Create demo data
python create_demo_data.py

# Run application
python app.py
```

Open http://localhost:5000 in your browser

## 📁 Project Structure

```
FinanzApp/
├── app.py                  # Entry point
├── config.py              # Configuration
├── database.py            # DB management
├── routes/                # Flask Blueprints
│   └── dashboard.py
├── services/              # Business logic
│   └── proyeccion.py
├── templates/             # HTML templates
└── finanzas.db           # Database
```

## 🎮 Basic Usage

1. **Initial setup**: Set initial balance and payment dates
2. **Register recurring income**: Salary, bonuses, etc.
3. **Add expenses**: Credit cards, loans, installment payments
4. **Check projections**: Visual dashboard with traffic light system
5. **Simulate purchases**: Before making financial commitments

## 🚀 Free Deployment

### Railway
1. Upload your code to GitHub
2. Connect on Railway.app
3. Automatic deployment

### Render
1. New Web Service on Render.com
2. Connect repository
3. Build: `pip install flask python-dateutil`
4. Start: `python app.py`

## 🤝 Contributions

Contributions are welcome! Open an Issue or Pull Request.

## 📄 License

MIT License - see LICENSE for details

---

**Made with ❤️ in Mexico**
