#!/usr/bin/env python2.7

"""
Columbia W4111 Intro to databases
Example webserver

To run locally

    python server.py

Go to http://localhost:8111 in your browser


A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, url_for

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)



# XXX: The Database URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@<IP_OF_POSTGRE_SQL_SERVER>/<DB_NAME>
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@<IP_OF_POSTGRE_SQL_SERVER>/postgres"
#
# For your convenience, we already set it to the class database

# Use the DB credentials you received by e-mail
DB_USER = "jf3355"
DB_PASSWORD = "jia123"

DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"

DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/proj1part2"


#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)


# Here we create a test table and insert some values in it
engine.execute("""DROP TABLE IF EXISTS test;""")
engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")



@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request

  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to e.g., localhost:8111/foobar/ with POST or GET then you could use
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like
  print(request.args)
  curr_admin = request.args.get('curr_admin')
  plate = request.args.get('plate')
  owner = request.args.get('owner')
  paid = request.args.get('paid')

  #
  # example of a database query
  #
  cursor = g.conn.execute("SELECT id, address FROM Lots WHERE manager = %s", curr_admin)
  lots_id = [] 
  lots_addr = []
  for result in cursor: # can also be accessed using result[0]
    lots_id.append(result['id'])
    lots_addr.append(result['address'])
  cursor.close()

  lots_spot_num = []
  for id in lots_id:
    cursor = g.conn.execute("SELECT COUNT(id) AS count FROM Spots WHERE lot_id = %s", id)
    results = []
    for result in cursor:
      results.append(result['count'])
    cursor.close()

    lots_spot_num.append(results[0])

  #
  # Flask uses Jinja templates, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
  #
  # You can see an example template in templates/index.html
  #
  # context are the variables that are passed to the template.
  # for example, "data" key in the context variable defined below will be 
  # accessible as a variable in index.html:
  #
  #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
  #     <div>{{data}}</div>
  #     
  #     # creates a <div> tag for each element in data
  #     # will print: 
  #     #
  #     #   <div>grace hopper</div>
  #     #   <div>alan turing</div>
  #     #   <div>ada lovelace</div>
  #     #
  #     {% for n in data %}
  #     <div>{{n}}</div>
  #     {% endfor %}
  #
  context = dict(
    lots_id = lots_id,
    lots_addr = lots_addr, 
    lots_spot_num = lots_spot_num,
    email = curr_admin,
    len = len(lots_id),
    plate = plate,
    owner = owner,
    paid = paid
  )


  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  return render_template("index.html", **context)

#
# This is an example of a different path.  You can see it at
# 
#     localhost:8111/another
#
# notice that the functio name is another() rather than index()
# the functions for each app.route needs to have different names
#
@app.route('/another')
def another():
  return render_template("anotherfile.html")


# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
  address = request.form['address']
  email = request.form['email']
  print(address)
  cmd = 'INSERT INTO Lots(address, manager) VALUES (:addr, :manager)';
  g.conn.execute(text(cmd), addr = address, manager = email);
  return redirect(url_for('index', curr_admin = email))

@app.route('/addviolation', methods=['POST'])
def add_violation():
  spot = request.form['spot']
  car = request.form['car']
  amount = request.form['amount']
  email = request.form['email']
  cmd = 'INSERT INTO Violations(spot_id, car_plate, amount, paid) VALUES (:spot, :car, :amount, false)';
  g.conn.execute(text(cmd), spot = spot, car = car, amount = amount);
  return redirect(url_for('index', curr_admin = email))


@app.route('/removeviolation', methods=['POST'])
def remove_violation():
  id = request.form['id']
  email = request.form['email']
  print(id)
  g.conn.execute('UPDATE Violations SET paid=true WHERE id=%s', id);
  return redirect(url_for('index', curr_admin = email))


@app.route('/lookupcar')
def lookup_car():
  car_plate = request.args.get('carplate')
  email = request.args.get('email')
  cursor = g.conn.execute('SELECT email FROM Car_ownerships WHERE car_plate=%s', car_plate);
  results = []
  for result in cursor:
    results.append(result['email'])
  if len(results) > 0:
    return redirect(url_for('index', curr_admin = email, plate = car_plate, owner = results[0]))
  else:
    return redirect(url_for('index', curr_admin = email, plate = car_plate, owner = "NOT FOUND"))

@app.route('/lookuptransaction')
def lookup_transaction():
  id = request.args.get('id')
  email = request.args.get('email')
  print(id)

  cursor = g.conn.execute('SELECT paid FROM Transactions WHERE id=%s', id);
  results = []
  for result in cursor:
    results.append(result['paid'])

  if len(results) > 0:
    return redirect(url_for('index', curr_admin = email, paid = results[0]))
  else:
    return redirect(url_for('index', curr_admin = email, paid = "NOT FOUND"))

  

@app.route('/signup', methods=['POST'])
def signup():
  email = request.form['email']
  password = request.form['password']
  company = request.form['company']
  print(email)
  print(password)
  print(company)
  cmd = 'INSERT INTO Admin(email, password, company) VALUES (:email, :password, :company)';
  g.conn.execute(text(cmd), email = email, password = password, company = company);
  return redirect('/')


@app.route('/login')
def login():
  email = request.args.get('email')
  input_password = request.args.get('password')
  cmd = 'SELECT password FROM Admin WHERE email = %s';
  cursor  = g.conn.execute(cmd, [email]);
  correct_password = []
  for pwd in cursor:
    correct_password.append(pwd['password'])
  cursor.close()
  
  admin = ""
  
  if (input_password == correct_password[0]):
    print("success")
    admin = email
  else:
    print("failed")
    return redirect('/')
  
  return redirect(url_for('index', curr_admin = admin))


if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using

        python server.py

    Show the help text using

        python server.py --help

    """

    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
