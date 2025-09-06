from flask import Flask, render_template, request, flash, redirect, url_for, session
import mysql.connector
import re
import random


connection = mysql.connector.connect(
    host = 'luckyspin-1.czg4wmsiihb0.eu-west-3.rds.amazonaws.com',
    database = 'luckyspin',
    username = 'bambi15',
    password = 'Bambi7708#a'
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
           
           first_name, last_name = user['full_name'].split(" ", 1)
           session['display_name'] = f"{first_name[0].upper()}. {last_name.capitalize()}"
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
    
    return render_template("menu.html", display_name=session['display_name'],balance =session['balance'])

@app.route('/play', methods=['GET', 'POST'])
def play():
    if 'user_id' not in session:
        flash("Please login first!")
        return redirect(url_for('login'))

    # Create display_name from session full_name
    first_name, last_name = session['full_name'].split(" ", 1)
    display_name = f"{first_name[0].upper()}. {last_name.capitalize()}"

    if request.method == 'POST':
        try:
            bet_amount = float(request.form.get("amount"))
        except (ValueError, TypeError):
            flash("Invalid bet amount entered.")
            return render_template("play.html", 
                                   display_name=display_name, 
                                   balance=session['balance'])

        if bet_amount < 100 or bet_amount > session['balance']:
            flash("Bet must be between R100 and your balance")
            return render_template("play.html",
                                   display_name=display_name,
                                   balance=session['balance'])

        try:
            user_numbers = set()
            for i in range(1, 7):
                num = request.form.get(f"number{i}")
                if num is None or num == '':
                    flash("Please fill all 6 number fields")
                    return render_template("play.html",
                                           display_name=display_name,
                                           balance=session['balance'])
                user_numbers.add(int(num))
        except (ValueError, TypeError):
            flash("Enter valid numbers between 1 and 49")
            return render_template("play.html",
                                   display_name=display_name,
                                   balance=session['balance'])

        if len(user_numbers) != 6 or any(n < 1 or n > 49 for n in user_numbers):
            flash("Enter 6 unique numbers between 1 and 49")
            return render_template("play.html",
                                   display_name=display_name,
                                   balance=session['balance'])

        drawn_numbers = set(random.sample(range(1, 50), 6))
        match_count = len(user_numbers & drawn_numbers)

        outcome, winnings = "LOSS", 0
        if match_count == 6:
            outcome, winnings = "WIN", bet_amount * 100
        elif match_count == 3:
            outcome, winnings = "PARTIAL", bet_amount * 50

        new_balance = session['balance'] - bet_amount + winnings
        session['balance'] = new_balance

        try:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO lottodraw (draw_date, total_pool) VALUES (NOW(), %s)", (bet_amount,))
            draw_id = cursor.lastrowid

            for num in drawn_numbers:
                cursor.execute("INSERT INTO lottodraw_numbers (draw_id, number) VALUES (%s, %s)", (draw_id, num))

            cursor.execute("""
                INSERT INTO game (played_at, wager_amount, matched_numbers, winnings,
                                  player_id, outcome, draw_id)
                VALUES (NOW(), %s, %s, %s, %s, %s, %s)
            """, (bet_amount, match_count, winnings, session['user_id'], outcome, draw_id))
            game_id = cursor.lastrowid

            for num in user_numbers:
                cursor.execute("INSERT INTO game_chosennumbers (game_id, number) VALUES (%s, %s)", (game_id, num))

            cursor.execute("UPDATE participant SET balance=%s WHERE id=%s", (new_balance, session['user_id']))
            connection.commit()

        except mysql.connector.Error as err:
            flash(f"Database error: {err}")
            return render_template("play.html",
                                   display_name=display_name,
                                   balance=session['balance'])

        return render_template("game_result.html",
                               numbers=list(user_numbers),
                               drawn=list(drawn_numbers),
                               outcome=outcome,
                               winnings=winnings,
                               balance=new_balance)

    return render_template("play.html", 
                           display_name=display_name, 
                           balance=session['balance'])

    
#history. get the user from session!
@app.route('/history', methods=['GET', 'POST'])
def history():
    
    if 'user_id' not in session:
        flash("Not logged in.")
        return redirect(url_for('login'))
    #get session id
    user_id = session['user_id']
    #query
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM playergamehistory WHERE player_id = %s ORDER BY played_at DESC", (user_id, ))
    history_data = cursor.fetchall()
    cursor.close()
    return render_template("history.html", history = history_data)

#topup function here
@app.route('/topup', methods=['GET', 'POST'])
def topup():
    if 'user_id' not in session:
        flash("Log in")
        return redirect(url_for('login'))
    #get session id
    user_id = session['user_id']
    #
    if request.method == 'POST':
        try:
            amount = float(request.form.get("amount", 0))
        except ValueError:
            flash("Enter a valid amount. ")
            return render_template("topup.html")
        
        if amount < 100 or amount > 5000:
            flash("Top-up must be between R100 and R5000")
            return render_template("topup.html")
        try:
            cursor = connection.cursor()
            cursor.execute("UPDATE participant SET balance = balance + %s WHERE id = %s", (amount, user_id))
            connection.commit()
            cursor.close()
            session['balance'] = session['balance'] + amount

            flash(f"Successfully topped up R{amount:.2f}. New balance: R{session['balance']:.2f}")
            return redirect(url_for('menu'))
        except mysql.connector.Error as err:
            flash(f"Database error: {err}")
            return render_template("topup.html")
    return render_template("topup.html")


@app.route('/signup', methods=['POST', 'GET'])
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
        # create display name with first initial + surname
        display_name = f"{name[0].upper()}. {surname.capitalize()}"
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
        
        session['display_name'] = display_name
        return render_template("signup_success.html", full_name=fullname)
    
    except mysql.connector.Error as err:
        flash(f"Database error: {err}")
        return redirect(url_for('signup'))
    
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    msg = ''
    
    if request.method == 'POST':
        email = request.form.get('email')
        pswd1 = request.form.get('pswd1')
        pswd2 = request.form.get('pswd2')

        # Check required fields
        if not all([email, pswd1, pswd2]):
            flash("Fill in all fields!!")
            return redirect(url_for('forgot_password'))

        # Confirm match
        if pswd1 != pswd2:
            flash("Passwords do not match")
            return redirect(url_for('forgot_password'))

        # Length check
        if len(pswd2) < 8 or len(pswd2) > 12:
            flash("Password length must be between 8 - 12 characters")
            return redirect(url_for('forgot_password'))

        # Must contain uppercase + lowercase
        if not re.search(r'[A-Z]', pswd2) or not re.search(r'[a-z]', pswd2):
            flash("Password must contain both uppercase and lowercase letters")
            return redirect(url_for('forgot_password'))

        # Must contain a digit
        if not re.search(r'\d', pswd2):
            flash("Password must contain at least one number")
            return redirect(url_for('forgot_password'))

        # Must contain a special character
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'"\\|,.<>\/?]', pswd2):
            flash("Password must contain at least one special character")
            return redirect(url_for('forgot_password'))

        # Check if email exists
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM participant WHERE email=%s", (email,))
        account = cursor.fetchone()

        if not account:
            flash("No account with this email")
            cursor.close()
            return redirect(url_for('forgot_password'))

        # Update password
        cursor.execute("UPDATE participant SET p_password=%s WHERE email=%s", (pswd2, email))
        connection.commit()
        cursor.close()

        flash("Password reset successfully! You can now log in.")
        return redirect(url_for('login'))

    # GET request
    return render_template("forgot_password.html")

    
@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out. ")
    return render_template('home.html')
    
if __name__ == "__main__":
    app.run()