from flask import Flask, render_template, request, flash, redirect, url_for, session
import mysql.connector
import re


connection = mysql.connector.connect(
    host = 'localhost',
    database = 'LuckySpin',
    username = 'root',
    password = 'Mbambo1307#a'
)
#
cursor = connection.cursor()
app = Flask(__name__)
app.secret_key = "SoliderBoyRules"
def luhn_check(id_number):
    """Perform Luhn check on SA ID"""
    digits = [int(d) for d in id_number]
    odd_sum = sum(digits[-1::-2])
    even_digits = digits[-2::-2]
    even_sum = 0
    for d in even_digits:
        d *= 2
        even_sum += d // 10 + d % 10
    total = odd_sum + even_sum
    return total % 10 == 0


@app.route('/')
def home():
    return render_template("home.html")

@app.route('/login')
def login():
    return render_template("login.html")

@app.route('/login_customer',methods=['POST'])
def login_customer():
    msg = ''
    if request.method == 'POST':
        username = request.form.get('email')
        password = request.form.get('pswd1')
    
    if not all([username, password]):
       msg = "Fill in all required fields!!"
       flash(msg)
       return redirect(url_for('login'))
   
    try:
       cursor = connection.cursor(dictionary=True)
       query = "SELECT * FROM participant WHERE email=%s AND p_password=%s"
       cursor.execute(query, (username,password))
       user = cursor.fetchone()
       
       if user:
           update_query = "UPDATE participant SET last_login = NOW() WHERE email = %s"
           cursor.execute(update_query, (username,))
           connection.commit()
           #store dynamic values
           session['user_id'] = user['id']
           session['full_name'] = user['full_name']
           session['balance'] = float(user['balance'])
           
           flash(f"Welcome {user['full_name']}")
           return redirect(url_for('menu'))
       
       else:
           flash("Invalid email or password!")
           return redirect(url_for('login'))
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        flash("Something went wrong, please try again later.")
        return redirect(url_for('login'))
#game logic now
@app.route('/menu')
def menu():
    if 'user_id' not in session:
        flash("Please login first")
        return redirect(url_for('login'))
    
    return render_template("menu.html", full_name=session['full_name'],balance =session['balance'])
   

@app.route('/signup')
def signup():
    return render_template("signup.html")

@app.route('/signup_success')
def signup_success():
    return render_template("signup_success.html")

#participant signup
#only one email can signup
@app.route('/signup_customer', methods = ['POST'])
def signup_customer():
    msg = ''
    if request.method == 'POST':
        name = request.form.get('name')
        surname = request.form.get('surname')
        sa_id = request.form.get('sa_id')
        mobile = request.form.get('mobile_num')
        username = request.form.get('email')
        password1 = request.form.get('pswd1')
        password2 = request.form.get('pswd2')
#combine name and surname
        fullname = f"{name} {surname}"
#check 
    if not all([name,surname,sa_id,mobile,username,password1,password2]):
        msg = "Fill in all fields!!"
        flash(msg)
        return redirect(url_for('signup'))
#
    if password1 != password2:
        flash("Passwords do not match")
        return redirect(url_for('signup'))
    
    if not luhn_check(sa_id):
        flash("Invalid South African ID number")
        return redirect(url_for('signup'))
#check if email is pre-existing
    
    query = """INSERT INTO participant
                (sa_id, full_name, email, p_password, balance, mobile_number, created_at, last_login)
                VALUES (%s, %s, %s, %s, %s, %s, NOW(), NULL)"""
    values = (sa_id, fullname, username, password2, 2000.00, mobile)
    
    try:
        cursor.execute("SELECT * FROM participant WHERE email=%s", (username,))
        existing_user = cursor.fetchone()
        if existing_user:
            flash("Email is already signed up")
            return redirect(url_for('signup'))
        
        cursor.execute("SELECT * FROM participant WHERE sa_id=%s", (sa_id,))
        existing_sa_id = cursor.fetchone()
        if existing_sa_id:
            flash("South African ID already exists here")
            return redirect(url_for('signup'))
#check password
        if len(password2) < 8 or len(password2) > 12:
            msg = "Password length must be between 8 - 12 characters"
            flash(msg)
            return redirect(url_for('signup'))
        
        if not re.search(r'[A-Z]', password2) or not re.search(r'[a-z]', password2):
            msg = "Password must contain both uppercase and lowercase letters"
            flash(msg)
            return redirect(url_for('signup'))
        
        if not re.search(r'\d', password2):
            msg = "Password must contain at least one number"
            flash(msg)
            return redirect(url_for('signup'))
        
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'"\\|,.<>\/?]', password2):
            msg = "Password must contain at least one special character"
            flash(msg)
            return redirect(url_for('signup'))
        
        cursor.execute(query, values)
        connection.commit()
        return render_template("signup_success.html", full_name=fullname)
    
    except mysql.connector.Error as err:
        flash(f"Database error: {err}")
        return redirect(url_for('signup'))
    
if __name__ == "__main__":
    app.run(debug=True)
