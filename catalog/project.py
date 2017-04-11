import logging
import sys
import json
import random
import string
import httplib2
import requests
from flask import Flask, flash, jsonify, make_response, redirect, \
    render_template, request, session as login_session, url_for
from oauth2client.client import FlowExchangeError, flow_from_clientsecrets
from oauth2client.client import OAuth2WebServerFlow

from models import session, Category, Item
from permissions import Permissions
from users import UserUtils

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

app = Flask(__name__)

# -----------------------------------------------------------------------------
# USERS, AUTHENTICATION, and AUTHORIZATION

# TODO: finish moving all environment-sensitive values out of app code
config = json.loads(open('/webapps/catalog/client_secrets.json', 'r').read())
CLIENT_ID = config['web']['client_id']
CLIENT_SECRET = config['web']['client_secret']
APPLICATION_NAME = "Item Catalog"


@app.route(
    '/gconnect',
    methods=['POST'])
def gconnect():
    """
    Initiates user authentication via Google
    """
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = OAuth2WebServerFlow(
            client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
            scope='https://www.googleapis.com/auth/userinfo.profile')
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
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')

    if stored_access_token is not None and \
                    gplus_id == stored_gplus_id and \
                    'user_id' in login_session:
        return UserUtils.respond_with_preauthentication_url()

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()
    print data

    # Add user data fields to the session dictionary
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # Either create or retrieve the associated User
    # from the data store, by unique email
    user = UserUtils.try_get_user_by_email(data['email'])
    if not user:
        user = UserUtils.create_user(login_session)
    user_id = user.id
    login_session['user_id'] = user_id

    handle = UserUtils.get_user_handle()

    flash("you are now logged in as %s" % handle)
    print "done!"

    return UserUtils.respond_with_preauthentication_url()


@app.route(
    '/gdisconnect')
def gdisconnect():
    """
    Revokes a current Google user's token and resets their login_session
    """
    UserUtils.set_preauthentication_url()

    if 'access_token' not in login_session:
        return UserUtils.return_to_preauthentication_url()

    access_token = login_session['access_token']

    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']

    if access_token is None:
        print 'Access Token is None'
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % \
          login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    print 'result is '
    print result

    if result['status'] != '200':
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

    del login_session['access_token']
    del login_session['gplus_id']
    del login_session['username']
    del login_session['email']
    del login_session['picture']
    del login_session['user_id']

    return UserUtils.return_to_preauthentication_url()


@app.route(
    '/login')
def get_login_page():
    """
    Presents the user with the available authentication services, and
    creates a unique token
    """
    UserUtils.set_preauthentication_url()

    # Create anti-forgery state token
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for _ in range(32))

    login_session['state'] = state

    return render_template(
        'login.html',
        STATE=state)


# -----------------------------------------------------------------------------
# CATEGORY HTML ENDPOINTS

def extract_and_validate_category_name(form):
    """
    Returns the value and validaton error of the
    category name contained in the form
    :rtype: (String, String)
    """
    name = form.get('name')
    name_error = None

    if not name:
        name_error = 'Name is required'
    elif len(name) < 2 or len(name) > 80:
        name_error = 'Name must be between 2 and 80 characters'

    return name, name_error


@app.route(
    '/categories/create',
    methods=['GET', 'POST'])
def create_category():
    """
    HTML endpoint providing a form to create a new category
    """
    if not UserUtils.is_authenticated():
        UserUtils.set_preauthentication_url()
        flash('sign in to create categories')
        return redirect('/login')

    if request.method == 'POST':

        # Extract and validate the form inputs
        (name, name_error) = \
            extract_and_validate_category_name(request.form)

        if name_error:
            return UserUtils.render_user_template(
                'category_create.html',
                page_title="New Category",
                name=name, name_error=name_error)

        # Create the item in the data store

        item = Category(
            name=name,
            user_id=UserUtils.get_authenticated_user_id())
        session.add(item)
        session.commit()

        flash('category created')

        return redirect(url_for(
            'get_category_by_id',
            category_id=item.id))
    else:
        return UserUtils.render_user_template(
            'category_create.html',
            page_title="New Category")


@app.route('/')
@app.route('/categories/')
def get_categories():
    """
    HTML endpoint providing a list of all categories
    """
    try:
        items = session.query(Category).all()

        return UserUtils.render_user_template(
            'category_list.html',
            categories=items,
            page_title="Category List")
    except Exception as ex:
        logging.exception("get_categories")
        return "%s %s" % (ex.message, ex.args)


@app.route(
    '/categories/<int:category_id>/')
def get_category_by_id(category_id):
    """
    HTML endpoint providing details for a given category
    """
    category = session.query(Category).filter_by(id=category_id).one()

    items = session.query(Item).filter_by(category_id=category_id).all()

    return UserUtils.render_user_template(
        'category_items.html',
        category=category,
        items=items,
        page_title="%s Category" % category.name,
        can=Permissions.get_user_permissions_for_category(category))


@app.route(
    '/categories/<int:category_id>/update',
    methods=['GET', 'POST'])
def update_category_by_id(category_id):
    """
    HTML endpoint providing a form to edit a category
    """
    if not UserUtils.is_authenticated():
        UserUtils.set_preauthentication_url()
        flash('sign in to edit categories')
        return redirect('/login')

    category = session.query(Category).filter_by(id=category_id).one()

    if not Permissions.get_user_permissions_for_category(category).update:
        flash('you may edit only categories you created')
        return redirect(url_for(
            'get_categories'))

    if request.method == 'POST':
        # Extract and validate the form inputs
        (name, name_error) = \
            extract_and_validate_category_name(request.form)

        if name_error:
            return UserUtils.render_user_template(
                'category_update.html',
                category=category,
                page_title="%s %s Category" % ("Edit", category.name),
                name=name,
                name_error=name_error)

        # Create the item in the data store

        category.name = name
        session.add(category)
        session.commit()

        flash('category updated')

        return redirect(url_for(
            'get_category_by_id',
            category_id=category_id))
    else:
        return UserUtils.render_user_template(
            'category_update.html',
            category=category,
            page_title="%s %s Category" % ("Edit", category.name),
            name=category.name)


@app.route(
    '/categories/<int:category_id>/delete',
    methods=['GET', 'POST'])
def delete_category_by_id(category_id):
    """
    HTML endpoint providing a form to delete a category
    """
    if not UserUtils.is_authenticated():
        UserUtils.set_preauthentication_url()
        flash('sign in to delete categories')
        return redirect('/login')

    category = session.query(Category).filter_by(id=category_id).one()

    if not Permissions.get_user_permissions_for_category(category).delete:
        flash('you may delete only empty categories you created')
        return redirect(url_for(
            'get_categories'))

    if request.method == 'POST':
        session.delete(category)
        session.commit()

        flash('category deleted')

        return redirect(url_for(
            'get_categories'))
    else:
        return UserUtils.render_user_template(
            'category_delete.html',
            category=category,
            page_title="%s %s Category" % ("Delete", category.name))


# -----------------------------------------------------------------------------
# CATEGORY JSON ENDPOINTS

@app.route(
    '/api/categories/')
def api_get_categories():
    """
    API endpoint providing a list of all categories
    """
    categories = session.query(Category).all()

    def serialize(c):
        """
        Provides a representation of a category,
        suitable for conversion to JSON format
        """
        return {
            'id': c.id,
            'user_id': c.user_id,
            'name': c.name,
            'items_url': url_for(
                'api_get_items_by_category_id', category_id=c.id)
        }

    return jsonify(
        categories=[serialize(category) for category in categories])


@app.route(
    '/api/categories/<int:category_id>/')
def api_get_category(category_id):
    """
    API endpoint providing details for a given category
    """
    category = \
        session.query(Category).filter_by(id=category_id).one()

    items = \
        session.query(Item).filter_by(category_id=category_id).all()

    def serialize_item(i):
        """
        Provides a representation of an item,
        suitable for conversion to JSON format
        """
        return {
            'id': i.id,
            'user_id': i.user_id,
            'category_id': i.category_id,
            'url': url_for(
                'api_get_item_by_id',
                category_id=i.category_id, item_id=i.id),
            'title': i.title,
            'description': i.description
        }

    items = [serialize_item(item) for item in items]

    def serialize(c):
        """
        Provides a representation of a category,
        suitable for conversion to JSON format
        """
        return {
            'id': c.id,
            'user_id': c.user_id,
            'name': c.name,
            'items': items
        }

    return jsonify(
        category=serialize(category))


# -----------------------------------------------------------------------------
# ITEM HTML ENDPOINTS

def extract_and_validate_item_title(form):
    """
    Returns the value and validaton error of the
    item title contained in the form
    :rtype: (String, String)
    """
    title = form.get('title')
    title_error = None

    if not title:
        title_error = 'Title is required'
    elif len(title) < 2 or len(title) > 80:
        title_error = 'Title must be between 2 and 80 characters'

    return title, title_error


def extract_and_validate_item_description(form):
    """
    Returns the value and validaton error of the
    item description contained in the form
    :rtype: (String, String)
    """
    description = form.get('description')
    description_error = None

    if not description:
        description_error = 'Description is required'
    elif len(description) < 2 or len(description) > 80:
        description_error = 'Description must be between 2 and 250 characters'

    return description, description_error


@app.route(
    '/categories/<int:category_id>/items/create',
    methods=['GET', 'POST'])
def create_item(category_id):
    """
    HTML endpoint providing a form to create a new item within a category
    """
    if not UserUtils.is_authenticated():
        UserUtils.set_preauthentication_url()
        flash('sign in to create an item')
        return redirect('/login')

    category = \
        session.query(Category).filter_by(id=category_id).one()

    if request.method == 'POST':
        # Extract and validate the form inputs

        (title, title_error) = \
            extract_and_validate_item_title(request.form)

        (description, description_error) = \
            extract_and_validate_item_description(request.form)

        if title_error or description_error:
            return UserUtils.render_user_template(
                'item_create.html',
                category=category,
                category_id=category_id,
                title=title,
                title_error=title_error,
                description=description,
                description_error=description_error)

        # Create the item in the data store

        item = Item(
            title=title,
            description=description,
            category_id=category_id,
            user_id=UserUtils.get_authenticated_user_id())
        session.add(item)
        session.commit()

        flash('item created')

        return redirect(url_for(
            'get_category_by_id',
            category_id=category_id))
    else:
        return UserUtils.render_user_template(
            'item_create.html',
            category=category,
            category_id=category_id)


@app.route(
    '/categories/<int:category_id>/items/<int:item_id>/')
def get_item_by_id(category_id, item_id):
    """
    HTML endpoint providing details for a given item within a category
    """
    category = session.query(Category).filter_by(id=category_id).one()

    item = session.query(Item).filter_by(id=item_id).one()

    return UserUtils.render_user_template(
        'item_read.html',
        category=category,
        category_id=category_id,
        item=item,
        page_title="%s Item" % item.title,
        can=Permissions.get_user_permissions_for_item(item))


@app.route(
    '/categories/<int:category_id>/items/<int:item_id>/edit',
    methods=['GET', 'POST'])
def update_item_by_id(category_id, item_id):
    """
    HTML endpoint providing a form to edit an item
    """
    if not UserUtils.is_authenticated():
        UserUtils.set_preauthentication_url()
        flash('sign in to edit an item')
        return redirect('/login')

    item = session.query(Item).filter_by(id=item_id).one()

    # Users may update only items they created
    if not Permissions.get_user_permissions_for_item(item).update:
        flash('you may edit only items you created')
        return redirect(url_for(
            'get_category_by_id',
            category_id=category_id))

    category = session.query(Category).filter_by(id=category_id).one()

    if request.method == 'POST':
        # Extract and validate the form inputs

        (title, title_error) = \
            extract_and_validate_item_title(request.form)

        (description, description_error) = \
            extract_and_validate_item_description(request.form)

        if title_error or description_error:
            return UserUtils.render_user_template(
                'item_update.html',
                category=category,
                category_id=category_id,
                item=item,
                page_title="%s %s Item" % ("Edit", item.title),
                title=title,
                title_error=title_error,
                description=description,
                description_error=description_error)

        # Create the item in the data store

        item.title = title
        item.description = description
        session.add(item)
        session.commit()

        flash('item updated')

        return redirect(url_for(
            'get_category_by_id',
            category_id=category_id))
    else:
        return UserUtils.render_user_template(
            'item_update.html',
            category=category,
            category_id=category_id,
            item=item,
            page_title="%s %s Item" % ("Edit", item.title),
            title=item.title,
            description=item.description)


@app.route(
    '/categories/<int:category_id>/items/<int:item_id>/delete',
    methods=['GET', 'POST'])
def delete_item_by_id(category_id, item_id):
    """
    HTML endpoint providing a form to delete an item
    """
    if not UserUtils.is_authenticated():
        UserUtils.set_preauthentication_url()
        flash('sign in to delete an item')
        return redirect('/login')

    item = session.query(Item).filter_by(id=item_id).one()

    # Users may delete only items they created
    if not Permissions.get_user_permissions_for_item(item).delete:
        flash('you may delete only items you created')
        return redirect(url_for(
            'get_category_by_id',
            category_id=category_id))

    if request.method == 'POST':
        session.delete(item)
        session.commit()

        flash('item deleted')

        return redirect(url_for(
            'get_category_by_id',
            category_id=category_id))
    else:
        category = session.query(Category).filter_by(id=category_id).one()

        return UserUtils.render_user_template(
            'item_delete.html',
            category=category,
            category_id=category_id,
            item=item,
            page_title="%s %s Item" % ("Delete", item.title))


# -----------------------------------------------------------------------------
# ITEM JSON ENDPOINTS

@app.route(
    '/api/categories/<int:category_id>/items/')
def api_get_items_by_category_id(category_id):
    """
    API endpoint providing a list of all items within a given category
    """
    items = session.query(Item).filter_by(category_id=category_id).all()

    def serialize(i):
        """
        Provides a representation of an item,
        suitable for conversion to JSON format
        """
        return {
            'id': i.id,
            'url': url_for(
                'api_get_item_by_id',
                category_id=i.category_id,
                item_id=i.id),
            'user_id': i.user_id,
            'category_id': i.category_id,
            'title': i.title,
            'description': i.description
        }

    return jsonify(items=[serialize(item) for item in items])


@app.route(
    '/api/categories/<int:category_id>/items/<int:item_id>/')
def api_get_item_by_id(category_id, item_id):
    """
    API endpoint providing details for a given item within a category
    """
    item = session.query(Item). \
        filter_by(category_id=category_id, id=item_id). \
        one()

    def serialize_item(i):
        """
        Provides a representation of an item,
        suitable for conversion to JSON format
        """
        return {
            'id': i.id,
            'user_id': i.user_id,
            'category_id': i.category_id,
            'category_url': url_for(
                'api_get_category',
                category_id=i.category_id),
            'title': i.title,
            'description': i.description
        }

    return jsonify(item=serialize_item(item))


# -----------------------------------------------------------------------------
# APPLICATION ENTRY POINT

if __name__ == '__main__':
    app.secret_key = 'my_super_secret_app_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
