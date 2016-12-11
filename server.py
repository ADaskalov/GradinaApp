from flask import make_response, request, current_app, Flask, render_template, jsonify, Response
from functools import wraps
import pandas
from datetime import datetime, timedelta
import pyodbc
import yaml
import pytz

# DB Dump + edit
# DB installation file
# cash payments table
# user id
# Appearance
# beer between dates

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
	entry_time = datetime.now(pytz.timezone('Europe/Sofia'))
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
	entry_time = datetime.now(pytz.timezone('Europe/Sofia'))
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
	if len(sleeps)>0:
		sleeps['Nights'] = sleeps['end_date'] - sleeps['start_date']
	if u_id is None:
		return sleeps
	else:
		return sleeps.loc[sleeps['u_id'] == u_id, :]

def set_payment(u_id, amount, pmnt_type_id, entry_user, comment = None):
	
	dbCon = pyodbc.connect(dbString)
	dbCrsr = dbCon.cursor()
	entry_time = datetime.now(pytz.timezone('Europe/Sofia'))
	uploadQuery = """INSERT INTO dbo.payments (u_id, amount, pmnt_type_id, comment, entry_time, entry_user)
						VALUES (?,?,?,?,?,?)"""
	
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
		
def get_cash_payments():
	dbCon = pyodbc.connect(dbString)
	pmntQuery = """SELECT * FROM dbo.cash_payments """
	cash_payments = pandas.read_sql(pmntQuery, dbCon)
	return cash_payments
		
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

def stackScreen(screen, colList):
    stackedScreen = screen.copy()
    tmp = screen.copy()
    for x in colList:
        tmp2 = stackedScreen.copy()
        tmp2['Item'] = x
        tmp2['Value'] = stackedScreen[x]
        tmp = pandas.concat([tmp2,tmp],axis = 0)
        tmp.drop(x, axis = 1, inplace = True)

    return tmp[tmp['Item'].fillna(0)!=0]	

def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)

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
			<a href="http://karavana.party/debtoverview"> Debt Overview </a>
			<a href="http://karavana.party/sleepoverview"> Sleep Overview</a>
			<a href="%s"> Notes </a>
						
		</div>
	<br>
	"""%config['notesURL']
	
@app.route("/beeranalytics")
def beeranalytics():
	beers = get_beers()
	users = get_users()
	beers['Date'] = beers['entry_time'].map(lambda t: t.date())
	beers['Hour'] = beers['entry_time'].map(lambda t: t.hour)
	board = pandas.merge( left = beers, right = users, left_on = 'u_id', 
						right_index = True, how = 'outer')
	return render_template('pivottablejs.html', pyOutput = board.to_csv(), pctThreshold=0,
								rows = '"name"', cols = '"Date"', rendName = 'Table',
								aggName = 'Sum', aggVal = 'no_beers')
								
@app.route("/debtoverview")
def debtoverview():
	beers = get_beers().groupby('u_id').sum()
	users = get_users()
	sleeps = get_sleeps()
	cash_payments = get_cash_payments()
	sleeps['Nights'] = sleeps['Nights'].map(lambda t: t.days)
	sleeps['Nights_owed'] = sleeps['Nights']*sleeps['tent_id'].map(lambda t: 15 if pandas.isnull(t) else 5)*(sleeps['end_date']<datetime(2016,9,1))
	sleeps = sleeps.groupby('u_id').sum()
	payments = get_payments().groupby('u_id').sum()
	#TODO pivot payments
	debts = pandas.merge( left = users, right = beers, left_index = True, right_index = True, how = 'outer')
	debts = pandas.merge( left = debts, right = sleeps, left_index = True, right_index = True, how = 'outer')
	debts = pandas.merge( left = debts, right = payments, left_index = True, right_index = True, how = 'outer')
	debts['outstanding'] = debts['amount'].fillna(0) - debts['Nights_owed'].fillna(0) - debts['no_beers'].fillna(0)
	debts['Type'] = 'People'
	
	cash_payments.rename(columns = {'description' : 'name'}, inplace = True)
	cash_payments['Type'] = 'Other'
	debts = pandas.concat([debts, cash_payments], axis = 0)
	debts['amount'] = -debts['amount']
	stackedDebt = stackScreen(debts, [ 'no_beers', 'Nights_owed', 'amount'] )
	return render_template('pivottablejs.html', pyOutput = stackedDebt.loc[:,['Type', 'outstanding', 'name', 'Item', 'Value']].to_csv(), 
								pctThreshold=0,	rows = '["name", "Type"]', cols = '"Item"', rendName = 'Table',
								aggName = 'Sum', aggVal = 'Value')

@app.route("/sleepoverview")
def sleepoverview():
	users = get_users()
	sleeps = get_sleeps()
	sleeps = pandas.merge(left = sleeps, right = users, left_on = 'u_id', right_index = True, how = 'left').set_index('s_id')
	sleepOverview = pandas.DataFrame(columns = ['Name', 'date','tent_id'])
	i = 0
	for r in sleeps.index:
		for d in daterange(sleeps.ix[r,'start_date'], sleeps.ix[r,'end_date']):
			sleepOverview.loc[i] = [sleeps.ix[r,'name'],d.date(),sleeps.ix[r, 'tent_id']]
			i +=1
			
	return render_template('pivottablejs.html', pyOutput = sleepOverview.to_csv(), pctThreshold=0,
								rows = '"tent_id"', cols = '"date"', rendName = 'Table',
								aggName = 'Count', aggVal = 'Value')
								

@app.route("/beerboard")
@app.route("/")
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
			  <th>Name</th>
			  <th>Beers</th>
			  <th>Add</th>
			</tr>
		  </thead>
		  <tbody class = "list">"""
	for u in board.index:
		if board.ix[u,'photo_path'] == 0:
			PhotoSrc = 'nophoto.jpg'
		else:
			PhotoSrc = board.ix[u, 'photo_path']
		beerTable = beerTable + """
		<tr>
		  <td><img src = "/static/Photos/{PhotoSrc}" alt="{name}"  width="100"></td>
		  <th><a href="http://{appUrl}/profile/{u_id}" class = "name">{name}</a></th>
		  <td>{no_beers}</td>
		  <td><button type="button" onclick="addBeer({u_id})" style="height:40px;width:40px" >+1</button></td>
		  
		</tr>""".format(u_id = u, name = board.ix[u,'name'], no_beers = board.ix[u, 'no_beers'], appUrl = appUrl, PhotoSrc = PhotoSrc)
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
	userBeers['batch_id'] = userBeers['batch_id'].fillna('Burgasko')
	userBeers = userBeers.groupby(['Date', 'batch_id']).sum().loc[:, ['no_beers']]
	
	
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

mode = config['mode']
if mode == 'Prod':
	appUrl = 'karavana.party'
else:
	appUrl = 'localhost:5000'

if __name__ == "__main__":
    # here is starting of the development HTTP server

	
	if mode == 'Prod':
		appUrl = 'karavana.party'
		app.run(debug = False, host = '0.0.0.0', port = 80)
	else:
		appUrl = 'localhost:5000'
		app.run(debug = True)