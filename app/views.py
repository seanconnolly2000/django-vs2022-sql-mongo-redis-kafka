"""
Definition of views.
"""

from datetime import datetime
from django.shortcuts import render
from django.contrib.auth import authenticate, login as login_auth, logout, get_user_model
from django.contrib.auth.models import Group
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.views.decorators.http import require_http_methods

from .forms import SignupForm, LoginForm
from .apis import apis
from .mongo import data_wrapper, MongoDatabase
from .redis import SessionStore
from .kafka import Kafka
User = get_user_model() #app.User, not Auth.User from auth.models


# Architecture: 
#   Assumptions: 
#      Will be deployed on autoscale web/api cluster (session stored in Redis).
#      SQL Server, MongoDB, Redis, Kafka
#      Realtime data stored in Mongo should be aggregated to a data warehouse.
#   Application deployed via Dockers - docker-compose.yml for Kafka, Redis 
#       Could be used for SQL Server/Mongo/App but this is a demo.
#    
# User Model discussion:
#   The user model was extended from AbstractUser.
#   It now allows for federation id capability (login with 
#   Google/Facebook/LinkedIn - not implemented).  
#   The model uses signals/receiver to create a 
#   "User Profile" table to separate authentication from 
#   general user data.
#   While the Django Authentication model is used:
#   User-UserGroup-Group.  Currently, a 1:1 user-usergroup-group
#   is used to allow for future growth (linking many users to a single
#   group, which could be a Company/Org/etc.). Additionally,
#   the Django permission attributes can be utilized as needed. 
#   Functionality is attached to the group, not the user.
# Authentication Database:
#   SQL Server - swappable for MariaDB/Postgres/Whatever.
# Redis Sessions:
#   Session middleware is implemented using Redis to 
#   reduce SQL server load. 
#   NOTE: Once logged in, the SQL Server can actually be 
#   stopped and the sessions/authentication continues to function.
# Data storage: 
#   MongoDB is the datastore (for API views here). While not
#   implemented, this is where data from probes will be
#   stored.  Reports can be queried from MongoDB, however,
#   a longterm better approach would be to ETL the 
#   aggregated data to an offline SQL data warehouse. 
# Event Stream:
#   Kafka is the event message stream.  In this simple example,
#   Kafka is implemented to store the API data prior to inserting
#   it into MongoDB. In a real-world scenario, web servers produce 
#   events and separate processes will consume the events, protecting 
#   the MongoDB server during peaks and establishing a FIFO order 
#   to data from the web server cluster.
#   Kafka could also be utilized as a "push" event stream for outbound alerts, 
#   although not implemented in this prototype.



@require_http_methods(["GET"])
def home(request):
    global_metrics = None
    errors = []
    if 'username' in request.session:  #not using is_authenticated to prevent hit to SQL Server
        # The following illustrates:
        # 1. Accessing an API (you'll need to add the API and you API Key in APIs.py).
        # 2. Sending event to Kafka. 
        # 3. Retrieving event from Kafka.
        #        In production, events would be consumed by a service to facilitate:
        #        a. FIFO database actions over multiple web servers.
        #        b. Throttling should the database be at capacity.
        # 4. Inserting data into MongoDB document database.
        try:
            api = apis()
            api_data = api.service()
            if api_data:
                json_data = api_data['json_data']
                id = request.session['personal_group_id'] 
                if id is not None:
                    # format api data with a group id for mongodb
                    json_doc_with_group_id = data_wrapper(id, json_data)

                    k = Kafka()
                    # assumption: Web servers will be an autoscale cluster 
                    # with hundreds or thousands of machines at peak times.
                    # API info sent to Kafka stream to protect 
                    # production MongoDB during peak periods.
                    k.produceKafkaEvent("mongo_insert", json_doc_with_group_id.__dict__)
            
                    # obviously, we would never retrieve the 
                    # data we just sent to the event stream within the 
                    # same process.  Below saves/retrieves for this demo
                    # Kafka is queried, an array of items is retrieved, 
                    # and subsequently inserted into MongoDB.
                    array_of_docs_to_insert = k.consumeKafkaEvent("mongo_insert")
                    # Send unstructured data to mongodb.
                    db = MongoDatabase()
                    for doc in array_of_docs_to_insert:
                        db.insert("mongodb_collection", doc)  #Change to the target collection
        except Exception as e:
                # for demo only - do not display internal errors!
                errors.append("Error retrieving data from service: " + str(e))
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/index.html',
        {
            'title':'Home Page',
            'year':datetime.now().year,
            'errors' : errors
        }
    )







@require_http_methods(["GET"])
def contact(request):
    """Renders the contact page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/contact.html',
        {
            'title':'Contact',
            'message':'Your contact page.',
            'year':datetime.now().year,
        }
    )

@require_http_methods(["GET"])
def about(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/about.html',
        {
            'title':'About',
            'message':'Your application description page.',
            'year':datetime.now().year,
        }
    )


@require_http_methods(["POST", "GET"])
def signup(request):
    form = SignupForm()
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            bio = form.cleaned_data['bio']
            try:
                user = User.objects.create_user(username=username, password=password)
                user.save()
                user.profile.bio = bio # example of extended user data in Profile table
                user.profile.save()
                # NOTE: A group of 1 is initially created to allow data to be saved
                # at the group level, not the user level.  A group could be a 
                # company with many users attached.
                group, created = Group.objects.get_or_create(name=user.pk)
                group.user_set.add(user)
                auth_login_session(request, username, password)
                return HttpResponseRedirect('/')
            except Exception as e:
                # for demo only - do not display internal errors!
                form.add_error(None, f"We were unable to create an account for user {username}:" + str(e))
    return render(request, 'app/signup.html', {'form':form})

@require_http_methods(["POST", "GET"])
def login(request):
    form = LoginForm() 
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            if auth_login_session(request, username, password):
               return HttpResponseRedirect('/')
            else:
               form.add_error(None, "Invalid Username or Password.")
    return render(request, 'app/login.html', {'form': form})
    


def auth_login_session(request, username, password):
        # This common function is required for both Login and Signup
        # to establish important session items like personal_group_id
        # TODO: Move to authentication file.
        user = authenticate(request, username=username, password=password)
        if user is None:
            return False
        try:
            login_auth(request, user)
            request.session.set_expiry(300)
            request.session['username'] =  user.username
            request.session['first_name'] =  user.first_name  # yes, I know we didn't capture these in Signup :-)
            request.session['last_name'] =  user.last_name
            # TODO: extend Group to not rely on name attribute (perhaps have a "system group" flag)
            group = request.user.groups.filter(name=user.pk) # QuerySet
            if group[0]:
                request.session['personal_group_id'] = group[0].id 
            else:
                request.session['personal_group_id'] = None
     
            return True
        except Exception as e:
            return False
      