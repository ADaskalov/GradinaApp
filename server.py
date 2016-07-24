from flask import make_response, request, current_app, Flask, render_template, jsonify, Response
import pandas
from datetime import datetime
import pyodbc
import yaml

# DB Dump + edit
# sleep overview
# user id
# Appearance

with open('C:/Gradina App/config.yaml', 'r') as f:
	config = yaml.load(f)

dbString = config['dbCreds']
			
def set_user(name, photo_path = None):
	dbCon = pyodbc.connect(dbString)
	dbCrsr = dbCon.cursor()
	uploadQuery = """INSERT INTO dbo.users (name, photo_path) VALUES (?,?)"""
	
	try:
		dbCrsr.execute(uploadQuery, (name, photo_path))
		dbCrsr.commit()
		dbCon.close()
		return name + ' added'
	except Exception as e:
		dbCon.close()
		if 'duplicate key' in str(e):
			return 'Name already exists'
		else:
			return str(e)

def get_users(u_id = None):
	dbCon = pyodbc.connect(dbString)
	userQuery = """SELECT * FROM dbo.users"""
	users = pandas.read_sql(userQuery, dbCon).set_index('u_id')
	dbCon.close()
	if u_id is None:
		return users
	else:
		return users[u_id]

def set_beer(u_id, no_beers, entry_user, batch_id = None):
	dbCon = pyodbc.connect(dbString)
	dbCrsr = dbCon.cursor()
	entry_time = datetime.now()
	uploadQuery = """INSERT INTO dbo.beers (u_id, no_beers, entry_time, entry_user, batch_id)
						VALUES (?,?,?,?,?)"""
	
	try:
		dbCrsr.execute(uploadQuery, (u_id, no_beers, entry_time, entry_user, batch_id))
		dbCrsr.commit()
		dbCon.close()
		return no_beers + ' beers added'
	except Exception as e:
		dbCon.close()
		if 'duplicate key' in str(e):
			return 'Beer already exists'
		else:
			return str(e)

		
def get_beers(u_id = None):
	dbCon = pyodbc.connect(dbString)
	beerQuery = """SELECT * FROM dbo.beers """
	beers = pandas.read_sql(beerQuery, dbCon, parse_dates = ['entry_time'])
	if u_id is None:
		return beers
	else:
		return beers.loc[beers.u_id == u_id]

def set_sleep(u_id, start_date, end_date, entry_user, tent_id = None):
	dbCon = pyodbc.connect(dbString)
	dbCrsr = dbCon.cursor()
	entry_time = datetime.now()
	uploadQuery = """INSERT INTO dbo.sleeps (u_id, start_date, end_date, entry_time, entry_user, tent_id)
						VALUES (?,?,?,?,?,?)"""
	
	try:
		dbCrsr.execute(uploadQuery, (u_id, start_date, end_date, entry_time, entry_user, tent_id))
		dbCrsr.commit()
		dbCon.close()
		return 'Success'
	except Exception as e:
		dbCon.close()
		if 'duplicate key' in str(e):
			return 'Entry already exists'
		else:
			return str(e)
		
def get_sleeps(u_id = None): 
	dbCon = pyodbc.connect(dbString)
	sleepQuery = """SELECT * FROM dbo.sleeps"""
	sleeps = pandas.read_sql(sleepQuery, dbCon,parse_dates = ['entry_time', 'start_date', 'end_date'])
	print sleeps
	if len(sleeps)>0:
		sleeps['Nights'] = sleeps['end_date'] - sleeps['start_date']
	if u_id is None:
		return sleeps
	else:
		return sleeps.loc[sleeps['u_id'] == u_id, :]

def set_payment(u_id, amount, pmnt_type_id, entry_user, comment = None):
	
	dbCon = pyodbc.connect(dbString)
	dbCrsr = dbCon.cursor()
	entry_time = datetime.now()
	uploadQuery = """INSERT INTO dbo.payments (u_id, amount, pmnt_type_id, comment, entry_time, entry_user)
						VALUES (?,?,?,?,?,?)"""
	
	print uploadQuery
	try:
		dbCrsr.execute(uploadQuery, (u_id, amount, pmnt_type_id, comment, entry_time, entry_user))
		dbCrsr.commit()
		dbCon.close()
		return 'Success'
	except Exception as e:
		dbCon.close()
		if 'duplicate key' in str(e):
			return 'Entry already exists'
		else:
			return str(e)
		
def get_payments(u_id = None):
	dbCon = pyodbc.connect(dbString)
	pmntQuery = """SELECT * FROM 
			dbo.payments p JOIN 
			dbo.payment_types t
			ON p.pmnt_type_id = t.pmnt_type_id """
	payments = pandas.read_sql(pmntQuery, dbCon, parse_dates = ['entry_time']).drop('pmnt_type_id', axis = 1)
	if u_id is None:
		return payments
	else:
		return payments.loc[payments.u_id == u_id]
		
def get_payment_type_id(payment_type = None):
	dbCon = pyodbc.connect(dbString)
	pmntQuery = """SELECT * FROM dbo.payment_types """
	payment_types = pandas.read_sql(pmntQuery, dbCon).set_index('pmnt_type_desc')
	if payment_type is None:
		return payment_types
	else:
		if payment_type in payment_types.index:
			return payment_types.ix[payment_type, 'pmnt_type_id'].astype(int)
		else:
			return 'No such payment type'


from functools import wraps

def check_auth(u, p):
    """This function is called to check if a username /
    password combnation is valid.
    """
    return p == config['masterP']

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated
			
			
app = Flask(__name__)
@app.route("/home")
def home():
	return """
	<style>
		a:link, a:visited {
			background-color: #f44336;
			color: white;
			padding: 7px 25px;
			text-align: center; 
			text-decoration: none;
			display: inline-block;
			border-radius: 4px;
		}
		a:hover, a:active {
			background-color: red;
		}
	</style>
		<div align="center">
			<a href="http://karavana.party/beerboard"> Beer Leaderboard </a>
			<a href="http://karavana.party/beeranalytics"> Beer Analytics </a>
						
		</div>
	<br>
	"""
	
@app.route("/beeranalytics")
def beeranalytics():
	beers = get_beers()
	users = get_users()
	beers['Date'] = beers['entry_time'].map(lambda t: t.date())
	beers['Hour'] = beers['entry_time'].map(lambda t: t.hour)
	board = pandas.merge( left = beers, right = users, left_on = 'u_id', 
						right_index = True, how = 'outer')
	return render_template('pivottablejs.html', pyOutput = board.to_csv(), pctThreshold=0,
								rows = '"name"', cols = '"Date"', rendName = 'Line Chart',
								aggName = 'Sum', aggVal = 'no_beers')


@app.route("/beerboard")
def beerboard():
	beers = get_beers()
	users = get_users()
	
	board = pandas.merge( left = beers.groupby('u_id').sum(), right = users, left_index = True, 
						right_index = True, how = 'outer').fillna(0).sort_values('no_beers', ascending = False)


	beerTable  = """
		<table border="1" class="dataframe">
		  <thead>
			<tr style="text-align: right;">
			  <th></th>
			  <th>Beers</th>
			  <th>Add</th>
			</tr>
		  </thead>
		  <tbody class = "list">"""
	for u in board.index:
		beerTable = beerTable + """
		<tr>
		  <th><a href="http://{appUrl}/profile/{u_id}" class = "name">{name}</a></th>
		  <td>{no_beers}</td>
		  <td><button type="button" onclick="addBeer({u_id})" >+1</button></td>
		</tr>""".format(u_id = u, name = board.ix[u,'name'], no_beers = board.ix[u, 'no_beers'], appUrl = appUrl)
	beerTable = beerTable + "</tbody></table>"
	return render_template('beerboard.html', Board = beerTable, appUrl = appUrl)

@app.route("/addsleep", methods = ['POST','GET', 'OPTIONS'])
@requires_auth
def addSleep():
	u_id = request.form['u_id']
	start_date = datetime.strptime(request.form['start_date'],'%Y-%m-%d' )
	end_date = datetime.strptime(request.form['end_date'],'%Y-%m-%d' )
	entry_user = request.headers['Origin']
	return  set_sleep(u_id, start_date, end_date, entry_user)

@app.route("/addpayment", methods = ['POST','GET', 'OPTIONS'])
@requires_auth
def addPayment():
	u_id = request.form['u_id']
	amount = request.form['amount']
	pmnt_type_id = get_payment_type_id(request.form['type'])
	comment = request.form['comment']
	entry_user = request.headers['Origin']
	return set_payment(u_id, amount, pmnt_type_id, entry_user, comment)
	
@app.route("/addbeer", methods = ['POST','GET', 'OPTIONS'])
def addBeer():
	u_id = request.form['u_id']
	no_beers = request.form['no_beers']
	entry_user = request.headers['Origin']
	return  set_beer(u_id, no_beers, entry_user)

@app.route("/adduser", methods = ['POST','GET', 'OPTIONS'])
def addUser():
	name = request.form['name']
	photo_path = None if request.form['photo_path'] == '' else request.form['photo_path']
	return  set_user(name, photo_path)

def generate_profile(user, template):
	u_id = int(user)
	users = get_users()
	name = users.ix[u_id, 'name']
	photosrc = users.ix[u_id, 'photo_path']
	if pandas.isnull(photosrc):
		photosrc = 'nophoto.jpg'

	
	userSleeps = get_sleeps(u_id).loc[:,['start_date', 'end_date', 'tent_id', 'Nights']]
	
	userBeers = get_beers(u_id)
	userBeers['Date'] = userBeers['entry_time'].map(lambda t: t.date())
	userBeers = userBeers.groupby('Date').sum().loc[:, ['no_beers']]
	
	
	payments = get_payments(u_id)
	userPayments = payments.groupby('pmnt_type_desc').sum().loc[:, ['amount']]
	
	
	return render_template(template, Name = name, PhotoSrc = photosrc,
							Sleeps = userSleeps.to_html(index = False, index_names = False),
							Beers = userBeers.to_html(),
							Payments = userPayments.to_html(formatters = {'amount': '{0:,.2f} lv.'.format}),
							u_id = u_id, appUrl = appUrl)

							
@app.route("/profile/<user>") 
def profile(user):
	return generate_profile(user, 'profile.html')


@app.route("/masterprofile/<user>") 
@requires_auth
def masterprofile(user):
	return generate_profile(user, 'masterprofile.html')

if __name__ == "__main__":
    # here is starting of the development HTTP server
	mode = config['mode']
	if mode == 'Prod':
		appUrl = 'karavana.party'
		app.run(debug = False, host = '0.0.0.0', port = 80)
	else:
		appUrl = 'localhost:5000'
		app.run(debug = True)