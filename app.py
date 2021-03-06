# Create local web app with Flask, recieve a post request and send new order information to MS Teams
# 1. run server with python server.py
# 2. Send Post Request with response body similar to the one of woocommerce order created (or run webhook.py)
# 3. Magic 🧙‍️

# Code of your application, which uses environment variables (e.g. from `os.environ` or
# `os.getenv`) as if they came from the actual environment.
from dotenv import load_dotenv
import os

# pymsteams docs @ https://pypi.org/project/pymsteams/
import pymsteams

# Flask docs @ https://flask.palletsprojects.com/en/2.0.x/
from flask import Flask, request, render_template

# send emails from form
import smtplib

#create databse
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

from werkzeug.utils import redirect

# take environment variables from .env.
load_dotenv()

# initiate flask app and config database
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///orders.db"

# initialize the databse
db = SQLAlchemy(app)

#create db model
class Orders(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

# Create function to return string when we add something
def __rep__(self):
    return "<Name %r>" % self.id

    
subscribers = []

# using the incoming webhook connector in teams
# currently in the Sandbox Team > General Channel
# Config if necessary
teams_url = os.getenv("TEAMS_URL")

#link to shop inventory which appears on the connector card in teams
inventory_url = "https://teams.microsoft.com/l/entity/26bc2873-6023-480c-a11b-76b66605ce8c/_djb2_msteams_prefix_3731328403?context=%7B%22subEntityId%22%3Anull%2C%22channelId%22%3A%2219%3Ac0e11ad3197445e5b21885091f403d72%40thread.tacv2%22%7D&groupId=ca70fcdf-7ce6-4bed-be63-d4a1efcb5950&tenantId=76a44d37-80fd-4f78-9af8-9c6787de275e"

# You must create the connector card object with the Microsoft Webhook URL
myTeamsMessage = pymsteams.connectorcard(teams_url)


@app.route("/")
def index():

    name = "Alex"

    return render_template("index.html", name=name)

@app.route("/orders", methods=["POST", "GET"])
def orders():
    if request.method == "POST":
        order_name = request.form['name']
        new_order = Orders(name=order_name)
        # Push to databse
        try: 
            db.session.add(new_order)
            db.session.commit()
            return redirect("/orders")
        except:
            return render_template("orders.html")
    else:
        orders = Orders.query.order_by(Orders.date_created)
    return render_template("orders.html", orders=orders)

@app.route("/webhook", methods=["POST", "GET"])
def webhook():

    if request.method == 'POST':

        print("Webhook triggered!")
        # grab information from JSON Object
        total = request.json["total"]
        currency = request.json["currency"]
        fname = request.json["billing"]["first_name"]
        lname = request.json["billing"]["last_name"]
        product_list = request.json["line_items"]

        # loop through line_items and display quantity and price of each product bought
        # return a string of all necessary information for connector card
        def list_products():
            x = 1
            lists = []
            dname = "Donor: " + fname + " " + lname + " | "
            summary = " | Total: " + total + " " + currency
            for i in product_list:
                product = i["name"]
                quantity = i["quantity"]
                product_total = i["total"]
                purchase = "Product " + str(x) + ": " + str(quantity) + "x " + product + " for " + product_total + " " + currency
                x += 1
                lists.append(purchase)
            result = " | ".join(lists)
            return(dname + result + summary)

        # Create Connector Card
        # Add a title
        myTeamsMessage.title("Incoming Shop Donation")

        # Add text to the message
        txt = str(list_products())
        myTeamsMessage.text(txt)
        print(txt)

        # Add a link button
        myTeamsMessage.addLinkButton("View Inventory", inventory_url)

        # send the message.
        myTeamsMessage.send()

    return render_template("webhook.html")

@app.route("/subscribe")
def subscribe():

    return render_template("subscribe.html")

@app.route("/form", methods=["POST"])
def form():

    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    email = request.form.get("email")

    # create email message to subscriber /commented our due to athentication errors
    # need to register as safe app to google to work
    #message = "You have been subscribed to my email newsletter"
    #server = smtplib.SMTP("smtp.gmail.com", 587)
    #server.starttls()
    #server.login("","") -> (email, password)
    #server.sendmail("ajaeck@gmail.com", email)

    #form error hadling
    if not first_name or not last_name or not email:
        error_statement = "All Form Fields Required...😢"
        return render_template("subscribe.html", error_statement=error_statement, first_name=first_name, last_name=last_name,email=email )

    subscribers.append(f"{first_name} {last_name} {email}" )
    
    # Create Connector Card
    # Add a title
    myTeamsMessage.title("New Subscriber")

    # Add text to the message
    txt = "{} has subscribed to a newsletter with {}".format(first_name, email)
    myTeamsMessage.text(txt)
    print(txt)

    # Add a link button
    myTeamsMessage.addLinkButton("View Inventory", inventory_url)

    # send the message.
    myTeamsMessage.send()

    return render_template("form.html", first_name=first_name)