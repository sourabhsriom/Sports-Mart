from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy import create_engine, desc
from datetime import datetime
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
    user = session.query(User).filter_by(name = username).first()
    if not user or not user.verify_password(password):
        return False
    g.user = user
    return True


def createUser(login_session) :
    newUser = User(name = login_session['username'], email = login_session['email'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email = login_session['email']).one()
    return user.id

def getUserInfo(user_id) :
    user = session.query(User).filter_by(id = user_id).one()
    return user

def getUserId(email):
    try :
        user = session.query(User).filter_by(email = email).one()
        return user.id
    except :
        return None


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
    user_id = credentials.id_token['sub']
    if result['user_id'] != user_id:
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
    stored_user_id = login_session.get('user_id')
    if stored_access_token is not None and user_id == stored_user_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token


    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id = getUserId(login_session['email'])
    if not user_id :
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

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
        del login_session['user_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        #return  render_template('mainmenu.html', categories = categories, items = items, login_session = login_session)

        return redirect(url_for('HelloWorld'))
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/')
@app.route('/hello')
def HelloWorld():

    categories = session.query(Category).all()


    #items = session.query(catItem).order_by(catItem.updated_ts.desc()).all()

    items = (session.query(catItem.id, catItem.name.label('item_name'), catItem.description, catItem.category_id, Category.name).join(Category, catItem.category_id == Category.id).order_by(catItem.updated_ts.desc()).all())

    if 'username' not in login_session :
        return render_template('mainmenuPublic.html', categories = categories, items = items, login_session = login_session)

    return render_template('mainmenu.html', categories = categories, items = items, login_session = login_session)

@app.route('/<int:category_id>/')
def categoryItems(category_id):
    category = session.query(Category).filter_by(id = category_id).one()
    items = session.query(catItem).filter_by(category_id = category_id).all()
    categories = session.query(Category).all()

    if 'username' not in login_session or getUserId(login_session['email']) != category.user_id :
        return render_template('catmenuPublic.html', category = category, items = items, categories = categories)
    else:

        return render_template('catmenu.html', category = category, items = items, categories = categories)


@app.route('/<int:category_id>/new', methods = ['GET', 'POST'])
def addCategoryItem(category_id):

    if 'username' not in login_session :
        return redirect('/login')
    if request.method == 'POST' :
        newItem = catItem(name = request.form['name'], description = request.form['desc'], category_id = category_id)
        session.add(newItem)
        session.commit()
        flash("New item added!")
        return redirect(url_for('categoryItems', category_id = category_id))

    else :
        return render_template('add.html', category_id = category_id)

@app.route('/addNewItem', methods = ['GET', 'POST'])
def addNewItem():
    if request.method == 'POST':

        user_id = getUserId(login_session['email'])
        if user_id != session.query(Category).filter_by(name = request.form['category']).one().user_id :
            flash('User not permitted to modify this category')
            return redirect(url_for('addNewItem'))
        category_id = session.query(Category).filter_by(name = request.form['category']).one().id
        newItem = catItem(name = request.form['name'], description = request.form['desc'], category_id = category_id )
        session.add(newItem)
        session.commit()
        flash("New item added!")
        return redirect(url_for('HelloWorld'))
    else :
        return render_template('addNewItem.html')

@app.route('/<int:category_id>/<int:catItem_id>/')
def displayItem(category_id, catItem_id):
    item = session.query(catItem).filter_by(id = catItem_id).one()
    return render_template('item.html', item = item)

@app.route('/<int:category_id>/<int:catItem_id>/edit', methods = ['GET', 'POST'])
def editItem(category_id,catItem_id):
    cat = session.query(Category).filter_by(id = category_id).one()
    catname = cat.name
    categories = session.query(Category).all()
    editedItem = session.query(catItem).filter_by(id = catItem_id).one()
    if request.method == 'POST' :
        if request.form['name'] :
            editedItem.name = request.form['name']
        if request.form['desc'] :
            editedItem.description = request.form['desc']

        if request.form['newCategory'] :
            print ("name of new category is : ", request.form['newCategory'] )
            editedItem.category_id = session.query(Category).filter_by(name = request.form['newCategory']).one().id
        editedItem.updated_ts = datetime.utcnow()
        session.add(editedItem)
        session.commit()
        flash(editedItem.name + ' has been edited!')
        return redirect(url_for('categoryItems', category_id = category_id))
    else :
        return render_template('editItem.html', catItem_id = catItem_id, category_id = category_id, catname = catname, editedItem = editedItem, categories = categories)


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

@app.route('/addCategory/', methods = ['GET', 'POST'])
def addCategory():

    if 'username' not in login_session :
        return redirect('/login')
    if request.method == 'POST' :
        user_id = getUserId(login_session['email'])
        newCategory = Category(name = request.form['name'],user_id = user_id )
        session.add(newCategory)
        flash('New category created!')
        session.commit()
        return redirect('/hello')
    else :
        return render_template('addcategory.html')


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
