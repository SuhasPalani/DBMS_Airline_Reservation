import mysql.connector
from flask import Flask, redirect , render_template, request, flash
from flask.helpers import url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_login import login_required, login_user, logout_user, login_manager, LoginManager, current_user
from werkzeug.security import generate_password_hash, check_password_hash

#Flask 
local_server = True
app = Flask(__name__)
app.secret_key = 'Alpha'

#Login Credentials
login_manager = LoginManager(app)
login_manager.login_view= 'login'

#Database
# app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://username:password@localhost/database_name"
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://root:@localhost/airlines"


db = SQLAlchemy(app)

"""connection = mysql.connector.connect(host='localhost',
                                         database='airlines',
                                         user='root',
                                         password='')
cursor = connection.cursor()"""


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(20))
    email = db.Column(db.String(20), unique = True)
    dob = db.Column(db.Date)
    phone = db.Column(db.Integer)
    password = db.Column(db.String(1000))

class Flights( db.Model):
    fid = db.Column(db.String(10), primary_key = True)
    source = db.Column(db.String(50))
    destination = db.Column(db.String(50))
    date = db.Column(db.Date)
    time = db.Column(db.Time)
    airport_id = db.Column(db.Integer)
    price = db.Column(db.Integer)

class Bookings(db.Model):
    bid = db.Column(db.Integer, primary_key = True)
    uid = db.Column(db.Integer)
    fid = db.Column(db.String(10))
    seat = db.Column(db.String(10))
    mid = db.Column(db.Integer)
    totalamt = db.Column(db.Integer)

class Airport(db.Model):
    aid = db.Column(db.Integer, primary_key = True)
    aname = db.Column(db.String(50))

@app.route('/')
@app.route('/home')
def home():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/logindata', methods = ['POST', 'GET'])
def logindata():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            #flash('User Loged In', 'info')
            return render_template('services.html')
        else :
            flash('Invalid Credentials', 'danger')
            return render_template('login.html')
    else:
        return render_template('login.html')


@app.route('/signup')
def signup():
    return render_template ('signup.html')

@app.route('/signupdata', methods = ['POST', 'GET'])
def signupdata():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        dob = request.form.get('dob')
        phone = request.form.get('phone')
        password = request.form.get('password')
        encpassword = generate_password_hash(password)

        emailUser = User.query.filter_by(email=email).first()
        if emailUser:
            flash('Account for given email already exits, Please Login ', 'warning')
            return render_template('login.html')
        else:
            new_user = db.engine.execute (f"INSERT INTO `user` (`name`, `email`, `dob`, `phone`, `password`) VALUES ('{name}', '{email}', '{dob}', '{phone}', '{encpassword}' )")
            #user = User.query.filter_by(email=email).first()
            flash('User account created', 'success')
            return render_template('index.html')
    #return render_template ('signup.html.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout Sucessful', 'success')
    return redirect(url_for('home'))

@app.route('/bookings' , methods = ['POST', 'GET'])
@login_required
def bookings():
    uid = current_user.id
    userdata = User.query.filter_by(id=uid).first()
    
    if request.method == 'POST':
        uid = current_user.id
        fid = request.form['fid']
        flightdata = Flights.query.filter_by(fid=fid).first()
        aid = flightdata.airport_id
        print(aid)
        airportdata = Airport.query.filter_by(aid=aid).first()
        print(airportdata.aname)

        return render_template('bookings.html', userdata=userdata, flightdata=flightdata, airportdata=airportdata)
    else:
        return render_template('flights.html')

@app.route('/bookingsdata', methods = ['POST', 'GET'])
@login_required
def bookingsdata():
    if request.method == 'POST':
        uid = current_user.id
        fid = request.form.get('fid')
        sid = request.form.get('sid')
        mid = request.form.get('mid')
        
        print(sid)
        checkfid = Flights.query.filter_by(fid=fid).first()
        totalamt = checkfid.price
        if checkfid :
            bookingsdata = Bookings.query.filter_by(fid=fid)
            status = True
            for data in bookingsdata:
                if (sid == data.seat) :
                    status = False
                    flash('Selected Seat already booked', 'danger')
                    break
            if status:
                db.engine.execute (f"INSERT INTO `bookings` (`uid`, `fid`, `seat`, `mid`, `totalamt`) VALUES ('{uid}', '{fid}', '{sid}', '{mid}', '{totalamt}')")
                flash('Booking data stored', 'success')
                return redirect(url_for('orders'))
        else:
            flash('Invalid Flight ID', 'warning')
    return render_template('flights.html')

@app.route('/services')
@login_required
def services():
    return render_template('services.html')

@app.route("/flights", methods = ['POST', 'GET'] ) #search
@login_required
def flights():
    if request.method == 'POST':
        source = request.form.get('source')
        destination = request.form.get('destination')
        date = request.form.get('date')
        flightdata = Flights.query.filter_by(source=source, destination=destination, date=date)
        #print(flightdata)
        return render_template('flights.html', flightdata=flightdata)

    return render_template('flights.html')

@app.route('/orders', methods = ['POST', 'GET'])
@login_required
def orders():
    uid = current_user.id
    connection = mysql.connector.connect(host='localhost',
                                         database='airlines',
                                         user='root',
                                         password='')
    cursor = connection.cursor()
    #cursor = connection.cursor()
    results=cursor.callproc('orders', [uid, ])
    print (results)
    print("Printing assessment details")
    for result in cursor.stored_results():
        res=(result.fetchall())
    print(res)
    #print(orderdata)
    return render_template('orders.html', res=res)

@app.route('/edit/<string:bid>', methods = ['POST', 'GET'])
@login_required
def edit(bid):
    if request.method == 'POST':
        fid = request.form.get('fid')
        sid = request.form.get('sid')
        mid = request.form.get('mid')
        db.engine.execute ( f"UPDATE `bookings` SET  `fid`='{fid}' , `seat`='{sid}' , `mid`='{mid}' WHERE `bookings`.`bid`='{bid}' ")
        flash('Order Updated', 'success')
        return redirect('/orders')
        
    orders = Bookings.query.filter_by(bid=bid).first()
    return render_template('edit.html', orders=orders)

@app.route('/delete/<string:bid>', methods = ['POST', 'GET'])
@login_required
def delete(bid):
    db.engine.execute(f"DELETE FROM `bookings` WHERE `bookings`.`bid`='{bid}' ")
    flash('Order Deleted ', 'danger')
    return redirect(url_for('orders'))


app.run(debug=True)
