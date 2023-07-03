import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
import datetime
import pytz

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    #   Create a table with stock, amount of shares, current value of the share and the total value.
    #   Get the users id in the current session
    id = session.get("user_id")
    #   Get a table with all the stocks and total amount of shares per stock for this sessions user.
    table = db.execute("SELECT stock_symbol, SUM(shares) as total_shares FROM transactions WHERE user_id == ? GROUP BY stock_symbol;", id)
    ## If one of the rows has a value of 0 for the amount of shares, delete that row from the table
    i = 0
    while i < len(table):
        dict = table[i]
        if dict["total_shares"] == 0:
            table.remove(table[i])
            i = 0
        else:
            i += 1

    #   Get the users current balance
    cash = db.execute("SELECT cash FROM users WHERE id == ?", id)[0].get("cash")

    #   Add the key-value pairs for the current price and total value of each stock.

    for row in table:
        stock_info = lookup(row["stock_symbol"])
        current_price = stock_info.get("price")
        value = current_price * row["total_shares"]
        row["price"] = current_price
        row["total_value"] = value

    #   Calculate the total stocks value for this user
    total_stocks_value = 0

    for row in table:
        total_stocks_value += row["total_value"]

    total_assets = total_stocks_value + cash

    return render_template("index.html", summary_table = table, cash = usd(cash), total_assets = usd(total_assets) )


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        #   Get the stock requested by the user
        stock = request.form.get("symbol")
        print("stock: ", stock)

        #   Get a dictionary with the name, price and symbol of the required stock, via lookup()
        stock_info = lookup(stock)

        #   Check that the lookup() function didn't return none. Return html with required info.
        if stock_info:

            #   Calulate the total price for the user
            try: shares = int(request.form.get("shares"))
            except ValueError:
                return apology("Type in a positive integer for the amount of shares.")

            #   Check that the share are a positive integer
            if shares > 0 and  isinstance(shares, int):
                share_value = stock_info.get("price")
                price = shares * share_value
            else:
                return apology("Invalid amount of shares.")

            #   Calculate the balance of the user by substracting the total price from the actual balance.
             #   Get the user-id of the current session

            id = session.get("user_id")

             #   Get the current balance of the wallet related to this id.

            current_balance = db.execute("SELECT cash FROM users WHERE id == ?;", id)[0].get("cash")

             #   Calculate the new balance after buying.
            #   If this is smaller than zero, return apology.

            new_balance = current_balance - price

            if new_balance < 0:
                return apology("Not enough balance.")
            else:
                #   Update the new balance of the user
                db.execute("UPDATE users SET cash = ? WHERE id = ?;", new_balance, id)

                #   Store the transaction in the transacation database.
                now = datetime.datetime.now(pytz.timezone("US/Eastern"))
                db.execute("INSERT into transactions (user_id, stock_symbol, shares, price, time) VALUES (?, ?, ?, ?, ?);", id, stock, shares, share_value, now)

                #   Redirect to the homepage
                flash('Transaction successfull!')
                return redirect("/")

        else:
            return apology("This stock doesn't seem to exist, check the symbol")

    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    """Show portfolio of stocks"""
    #   Create a table with stock, amount of shares, current value of the share and the total value.
    #   Get the users id in the current session
    id = session.get("user_id")

    #   Get a table with all the stocks and total amount of shares per stock for this sessions user.
    table = db.execute("SELECT stock_symbol, shares, price, time FROM transactions WHERE user_id == ? ORDER BY time DESC;", id)

    return render_template("history.html", history_table = table)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        flash('Logged in!')
        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    #   If user submitted a request for a quote, check the quote and return information.
    if request.method == "POST":
        #   Get the stock requested by the user
        stock = request.form.get("symbol")

        #   Get a dictionary with the name, price and symbol of the required stock, via lookup()
        stock_value_dict = lookup(stock)

        #   Check that the lookup() function didn't return none.  Return html with required info.
        if stock_value_dict:

            name = stock_value_dict.get("name")
            price = stock_value_dict.get("price")
            symbol = stock_value_dict.get("symbol")

            return render_template("quoted.html", Name=name, Price=price, Symbol=symbol)

        else:
            return apology("This stock doesn't seem to exist, check its spelling.")

    #   When user accesses this path by clicking on the quote link, show user the quote form.
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username")
        rows = db.execute("SELECT * FROM users WHERE username == ?;", username)

        #   Check  the username
        if username == "" or username.isspace() == 1:
            return apology("Please fill in a username")

        elif len(rows) != 0:
            return apology("This username is already in use. Please choose another one.")

        #   Check the password
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if password == "" or password.isspace() == 1:
            return apology("Please fill in a valid password")

        elif password != confirmation:
            return apology("Passwords do not match")

        #   Hash the password
        pw_hash = generate_password_hash(password)

        #   Add the login details to the user database and redirect to the login page.

        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, pw_hash)

        #   Get the id of the user and log the user in.
        id_list = db.execute("SELECT id FROM users WHERE username == ?;", username)
        id = id_list[0]["id"]
        print("this id", id)
        session["user_id"] = id

        #   Give confirmation to the user that he has been successfully been registered.

        flash('Registration succesfull!')
        return redirect("/")


    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    #   Get all the symbols that are currently in the users wallet to give them the option to only sell one of these symbols.
    #   Also get the amount of shares the users owns, for reference
    id = session.get("user_id")
    table = db.execute("SELECT stock_symbol, SUM(shares) as total_shares FROM transactions WHERE user_id == ? GROUP BY stock_symbol;", id)
    print(table)

    if request.method == "POST":
        #   Get the symbol and amount of shares the users wants to sell
        symbol = request.form.get("symbol")
        print("Symbol: ", symbol)

        shares = request.form.get("shares")
        shares = int(shares)
        print("# shares: ", shares)

        # Per the construction of the form, the user can only select shares he owns, and has the input an mount of shares that is minimum equal to 1.
        # Just have to check if the amount of shares the user wants to sell is not more than the amount of shares the user has.

        max_shares = 0

        for row in table:
            if row["stock_symbol"] == symbol:
                max_shares = row["total_shares"]
        print("max shares: ", max_shares)

        if max_shares < shares:
            return apology("You don't have that many shares in your wallet.")
        #   If the user has enough shares, sell these shares at the current price.
        #   Increment the cash value in the database.
        #   Add the sale as a negative share in the transactions database.
        else:
            #   Get the current cash-balance of this user
            balance = db.execute("SELECT cash FROM users WHERE id == ?", id)[0].get("cash")
            print("balance: ", balance)

            #   Get the current price for the share the user wants to sell.
            price = lookup(symbol).get("price")
            print("price: ", price)

            #   Calculate the new balance after the sale.
            new_balance = balance + (shares * price)
            print("new balance", new_balance)

            # Update the users database with the new balance
            db.execute("UPDATE users SET cash = ? WHERE id = ?;", new_balance, id)

            # Store the transaction as a negative share in transactions database with a negative share
            now = datetime.datetime.now(pytz.timezone("US/Eastern"))
            db.execute("INSERT into transactions (user_id, stock_symbol, shares, price, time) VALUES (?, ?, ?, ?, ?);", id, symbol, -shares, price, now)

            #   Redirect to the homepage
            flash('Sale successfull!')
            return redirect("/")

    else:
        #   Only get the rows that don't have 0 shares
        i = 0
        while i < len(table):
            dict = table[i]
            if dict["total_shares"] == 0:
                table.remove(table[i])
                i = 0
            else:
                i += 1
        return render_template("sell.html", symbol_table = table)


@app.route("/profile", methods=["GET"])
@login_required
def profile():
    id = session.get("user_id")
    username = db.execute("SELECT username FROM users WHERE id == ?;", id)

    username = username[0].get('username')

    return render_template("profile.html", username=username)


@app.route("/changepw", methods=["GET", "POST"])
@login_required
def changepw():
    if request.method == "POST":
        id = session.get("user_id")
        old_password = request.form.get("old_password")
        new_password = request.form.get("set_new_password")
        new_password_confirmation = request.form.get("confirmation_new_password")
        db_password = db.execute("SELECT hash FROM users WHERE id == ?;", id)
        #   Check  the old password
        if check_password_hash(db_password[0]["hash"], old_password):
            #   Check if the new passwords match and are allowed
            if new_password == "" or new_password.isspace() == 1:
                return apology("Please fill in a valid password")

            elif new_password != new_password_confirmation:
                return apology("Passwords do not match")

            elif new_password == old_password:
                return apology("New password has to be different.")

            #   Hash the password
            pw_hash = generate_password_hash(new_password)

            #   Add the new password to the user database and redirect to the home page.
            db.execute("UPDATE users SET hash = ? WHERE id == ?;", pw_hash, id)

            #   Give confirmation to the user that the password wass changed and redirect to homepage.
            flash('Password changed succesfully!')
            return redirect("/")

        else:
                return apology("Wrong password")



    else:
        return render_template("changepw.html")


@app.route("/cash", methods=["GET", "POST"])
@login_required
def cash():
    if request.method == "POST":
        #   Check the amount that the user put in:
        amount = request.form.get("cash")

        try: amount = float(amount)
        except ValueError:
            return apology("Not a valid amount.")
        if amount < 0:
            return apology("Input a positive amount.")
        else:
            #   Add the amount to the existing cash of this user.
            id = session.get("user_id")
            current_balance = db.execute("SELECT cash FROM users WHERE id == ?", id)[0].get("cash")
            new_balance = current_balance + amount
            db.execute("UPDATE users SET cash = ? WHERE id = ?;", new_balance, id)

            #   Redirect to homepage
            flash('Amount added to wallet!')
            return redirect("/")

    else:
        return render_template("cash.html")
