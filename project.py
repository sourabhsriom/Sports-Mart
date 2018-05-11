from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dbsetup import Base, Category, catItem, User

from flask import session as login_session
import random, string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

from flask_httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()

app = Flask(__name__)


engine = create_engine('sqlite:///sportsmart.db?check_same_thread=False')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


CLIENT_ID = json.loads(open('client_secret.json', 'r').read())['web']['client_id']


@auth.verify_password
def verify_password(username, password):
    user = session.query(User).filter_by(username = username).first()
    if not user or not user.verify_password(password):
        return False
    g.user = user
    return True


@app.route('/newuser', methods = ['POST'])
def newUser():
    username = request.json.get("username")
    passwd = request.json.get("passwd")

    print (username)
    print (passwd)

    if not username or not passwd :
        abort(400)
    if session.query(User).filter_by(name = username).first() is not None :
        abort(400)
    user = User(name = username)
    user.hash_password(passwd)
    session.add(user)
    session.commit()
    return jsonify({"name" : user.name}), 201


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE = state)

@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secret.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print( "Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print( "done!")
    return output

@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print( 'Access Token is None')
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print( 'In gdisconnect access token is %s', access_token)
    print( 'User name is: ')
    print( login_session['username'])
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print( 'result is ')
    print( result)
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/')
@app.route('/hello')
def HelloWorld():
    category = session.query(Category).first()
    items = session.query(catItem).filter_by(category_id=category.id)
    return render_template('mainmenu.html', category = category, items = items)

@app.route('/<int:category_id>/')
def categoryItems(category_id):
    category = session.query(Category).filter_by(id = category_id).one()
    items = session.query(catItem).filter_by(category_id = category_id).all()

    return render_template('catmenu.html', category = category, items = items)


@app.route('/<int:category_id>/new', methods = ['GET', 'POST'])
@auth.login_required
def addCategoryItem(category_id):
    if request.method == 'POST' :
        newItem = catItem(name = request.form['name'], description = request.form['desc'], category_id = category_id)
        session.add(newItem)
        session.commit()
        flash("New item added!")
        return redirect(url_for('categoryItems', category_id = category_id))

    else :
        return render_template('add.html', category_id = category_id)



@app.route('/<int:category_id>/<int:catItem_id>/edit', methods = ['GET', 'POST'])
def editItem(category_id,catItem_id):
    cat = session.query(Category).filter_by(id = category_id).one()
    catname = cat.name
    editedItem = session.query(catItem).filter_by(id = catItem_id).one()
    if request.method == 'POST' :
        if request.form['name'] :
            editedItem.name = request.form['name']
        if request.form['desc'] :
            editedItem.description = request.form['desc']
        session.add(editedItem)
        session.commit()
        flash(editedItem.name + ' has been edited!')
        return redirect(url_for('categoryItems', category_id = category_id))
    else :
        return render_template('editItem.html', catItem_id = catItem_id, category_id = category_id, catname = catname, editedItem = editedItem)


@app.route('/<int:category_id>/<int:catItem_id>/delete', methods = ['GET', 'POST'])
def deleteItem(category_id, catItem_id):

    item = session.query(catItem).filter_by(id = catItem_id).one()

    if request.method == 'POST':
        session.delete(item)
        session.commit()
        flash(item.name + ' has been deleted')
        return redirect(url_for('categoryItems', category_id = category_id))
    else :
        return render_template('deleteItem.html', category_id = category_id, item = item)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)