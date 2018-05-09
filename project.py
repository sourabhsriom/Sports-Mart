from flask import Flask, render_template, request, redirect, url_for, flash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dbsetup import Base, Category, catItem

from flask import session as login_session
import random, string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)


engine = create_engine('sqlite:///sportsmart.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


CLIENT_ID = json.loads(open('client_secret.json', 'r').read())['web']['client_id']




@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    return render_template('login.html')


@app.route('/gconnect')
def gconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid State issue'), 401)
        response.header['Content-Type'] = 'application/json'
        return response
    code = request.data

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
