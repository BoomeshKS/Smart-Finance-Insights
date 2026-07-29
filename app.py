from flask import Flask, render_template, request, redirect, url_for, session
from db import init_db, reg_user, login_user, create_budget, get_budgets, get_all_budgets, update_budget, delete_budget
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

init_db()

@app.route('/')
def home():
    if 'uid' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['name']
        pwd = request.form['pwd']
        success, data = login_user(name, pwd)
        if success:
            session['uid'] = data['id']
            session['name'] = data['name']
            return redirect(url_for('dashboard'))
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html', error=None)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        pwd = request.form['pwd']
        if len(pwd) < 6:
            return render_template('register.html', error='Password must be at least 6 characters')
        success, result = reg_user(name, email, pwd)
        if success:
            return redirect(url_for('login'))
        return render_template('register.html', error=result)
    return render_template('register.html', error=None)

@app.route('/dashboard')
def dashboard():
    if 'uid' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', name=session['name'])

@app.route('/budgets', methods=['GET', 'POST'])
def budgets():
    if 'uid' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        action = request.form.get('action', 'create')
        cat = request.form['cat']
        month = request.form['month']
        
        if action == 'create':
            limit_amount = float(request.form['limit_amount'])
            success, err = create_budget(session['uid'], cat, limit_amount, month)
            if success:
                return redirect(url_for('budgets', month=month))
            return render_template('budgets.html', error=err, budgets=[], all_budgets=[], month=month)
        
        elif action == 'update':
            limit_amount = float(request.form['limit_amount'])
            success, err = update_budget(session['uid'], cat, limit_amount, month)
            if success:
                return redirect(url_for('budgets', month=month))
            return render_template('budgets.html', error=err, budgets=[], all_budgets=[], month=month)
        
        elif action == 'delete':
            success, err = delete_budget(session['uid'], cat, month)
            if success:
                return redirect(url_for('budgets', month=month))
            return render_template('budgets.html', error=err, budgets=[], all_budgets=[], month=month)
    
    month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    budgets = get_budgets(session['uid'], month)
    all_budgets = get_all_budgets(session['uid'])
    return render_template('budgets.html', budgets=budgets, all_budgets=all_budgets, month=month, error=None)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)