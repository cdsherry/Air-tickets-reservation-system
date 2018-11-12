from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = "dfdfdffdad"

# connect with database
conn = pymysql.connect(host='localhost',
                       user='root',
                       password='123456',
                       db='dbp',
                       cursorclass=pymysql.cursors.DictCursor)

cursor = conn.cursor()


@app.route('/')
def index():
    return render_template('index.html')


# Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    email = request.form['email']
    password = request.form['password']
    usertype = request.form['user']
    cursor = conn.cursor()
    # change to md5 format
    if usertype == 'customer':
        query = 'SELECT name FROM customer WHERE email = %s and password = md5(%s)'
    elif usertype == 'agent':
        query = 'SELECT booking_agent_id FROM booking_agent WHERE email = %s and password = md5(%s)'
    else:
        query = 'SELECT airline_name FROM airline_staff WHERE username = %s and password = md5(%s)'

    cursor.execute(query, (email, password))

    data = cursor.fetchone()
    cursor.close()
    error = None
    if data and usertype == 'customer':
        # creates a session for the customer
        # clear everything for session in case info from previous sessions are accessed
        session['airline'] = None
        session['id'] = None
        session['email'] = email
        name = data['name']
        session['username'] = name
        return redirect(url_for('home_customer'))

    elif data and usertype == 'staff':
        # creates a session for the airline staff
        session['email'] = None
        session['id'] = None
        session['username'] = email
        airline = data['airline_name']
        session['airline'] = airline
        return redirect(url_for('home_staff'))

    elif data and usertype == 'agent':
        # creates a session for the booking agent
        session['airline'] = None
        session['username'] = None
        session['email'] = email
        agent_id = data['booking_agent_id']
        session['id'] = agent_id
        return redirect(url_for('home_agent'))

    else:
        # returns an error message to the html page
        status = 'Invalid login or username'
        return render_template('login.html', status=status)


# Authenticates the register for customer
@app.route('/registerAuth_c', methods=['GET', 'POST'])
def registerAuth_c():
    status = "Succeed!"
    # grabs information from the users' input
    email = request.form['email']
    username = request.form['username']
    password = request.form['password']
    building_number = request.form['building_number']
    street = request.form['street']
    city = request.form['city']
    state = request.form['state']
    phone_number = int(request.form['phone_number'])
    passport_number = request.form['passport_number']
    passport_expiration = request.form['passport_expiration']
    passport_country = request.form['passport_country']
    date_of_birth = request.form['date_of_birth']

    cursor = conn.cursor()
    query1 = 'SELECT * FROM customer WHERE email = %s'
    query2 = 'SELECT * FROM booking_agent WHERE email = %s'
    cursor.execute(query1, email)
    data1 = cursor.fetchone()
    cursor.execute(query2, email)
    data2 = cursor.fetchone()

    error = None
    if data1 or data2:
        # If the previous query returns data, then user exists
        error = "This user already exists"
        return render_template('register_c.html', error=error)
    else:
        ins = 'INSERT INTO customer VALUES(%s, %s, md5(%s), %s, %s, %s, %s, %s, %s, %s, %s, %s)'
        try:
            cursor.execute(ins, (email, username, password, building_number, street, city, state, phone_number,
                                 passport_number, passport_expiration, passport_country, date_of_birth))
        except pymysql.err.DataError:
            status = "Please make sure that all inputs are in the correct format."
            return render_template('register_c.html', status=status)
        conn.commit()
        cursor.close()
        return render_template('index.html', status=status)


# Authenticates the register for booking agent
@app.route('/registerAuth_a', methods=['GET', 'POST'])
def registerAuth_a():
    status = "Succeed!"
    email = request.form['email']
    password = request.form['password']

    cursor = conn.cursor()
    query1 = 'SELECT * FROM customer WHERE email = %s'
    query2 = 'SELECT * FROM booking_agent WHERE email = %s'
    cursor.execute(query1, email)
    data1 = cursor.fetchone()
    cursor.execute(query2, email)
    data2 = cursor.fetchone()

    error = None
    if data1 or data2:
        # If the previous query returns data, then the user exists
        error = "This user already exists"
        return render_template('register_a.html', error=error)
    else:
        query0 = 'select max(booking_agent_id) as max from booking_agent'
        cursor.execute(query0)
        id = cursor.fetchall()[0]['max'] + 1
        ins = 'INSERT INTO booking_agent VALUES(%s, md5(%s), %s)'
        try:
            cursor.execute(ins, (email, password, id))
        except pymysql.err.DataError:
            status = "Please make sure that all inputs are in the correct format."
            return render_template('register_a.html', status=status)
        conn.commit()
        cursor.close()
        return render_template('index.html', status=status)


# Authenticates the register for airline staff
@app.route('/registerAuth_s', methods=['GET', 'POST'])
def registerAuth_s():
    status = "Succeed!"
    username = request.form['username']
    password = request.form['password']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    date_of_birth = request.form['date_of_birth']
    airline_name = request.form['airline_name']

    cursor = conn.cursor()
    query3 = 'SELECT * FROM airline_staff WHERE username = %s'
    cursor.execute(query3, username)
    data3 = cursor.fetchone()
    error = None
    if data3:
        # If the previous query returns data, then user exists
        error = "This user already exists"
        return render_template('register_s.html', error=error)
    else:
        # make sure that the airline exists
        query0 = 'select * from airline where airline_name = %s'
        cursor.execute(query0, airline_name)
        d = cursor.fetchone()
        if not (d):  # airline does not exist, then insert it first
            q_first = 'insert into airline values(%s)'
            cursor.execute(q_first, airline_name)
        ins = 'INSERT INTO airline_staff VALUES(%s, md5(%s), %s, %s, %s, %s)'
        try:  # error handling
            cursor.execute(ins, (username, password, first_name, last_name, date_of_birth, airline_name))
        except pymysql.err.DataError:
            status = "Please make sure that all inputs are in the correct format."
            return render_template('register_s.html', status=status)
        conn.commit()
        cursor.close()
        return render_template('index.html', status=status)


# With an input of an airport, return the airport
# With an input of a city, return a list of all the airports in the city.
def get_airport(location):
    airport = []
    cursor = conn.cursor()
    query = 'select * from airport where airport_name = %s'
    cursor.execute(query, location)
    result = cursor.fetchone()
    if result:
        airport.append(result['airport_name'])
    else:
        query = 'select airport_name from airport where airport_city = %s'
        cursor.execute(query, location)
        result = cursor.fetchall()
        if result:
            for item in result:
                airport.append(item['airport_name'])
    return airport


# Search flight publicly before login
@app.route('/search_flight', methods=['POST'])
def search_flight():
    source = request.form['departure_airport']
    arrival = request.form['arrival_airport']
    date = request.form['departure_date']
    cursor = conn.cursor()

    source = get_airport(source)
    arrival = get_airport(arrival)
    flights = []

    if date:
        for departure_airport in source:
            for arrival_airport in arrival:
                query = 'select * from flight where departure_airport = %s ' \
                        'and arrival_airport = %s and DATE(departure_time) = %s'
                cursor.execute(query, (departure_airport, arrival_airport, date))
                flights += cursor.fetchall()
    else:
        for departure_airport in source:
            for arrival_airport in arrival:
                query = 'select * from flight where departure_airport = %s and arrival_airport = %s'
                cursor.execute(query, (departure_airport, arrival_airport))
                flights += cursor.fetchall()
    cursor.close()
    return render_template('search_result.html', flights=flights)


# Search flight after login as a user
@app.route('/search_flight_login', methods=['POST'])
def search_flight_login():
    error = "Success!"
    source = request.form['departure_airport']
    # print(source)
    arrival = request.form['arrival_airport']
    date = request.form['departure_date']
    # use date: DONE
    cursor = conn.cursor()

    source = get_airport(source)
    arrival = get_airport(arrival)
    flights = []

    if date:
        for departure_airport in source:
            for arrival_airport in arrival:
                query = 'select * from flight where departure_airport = %s ' \
                        'and arrival_airport = %s and date(departure_time) = %s'
                cursor.execute(query, (departure_airport, arrival_airport, date))
                flights += cursor.fetchall()
    else:
        for departure_airport in source:
            for arrival_airport in arrival:
                query = 'select * from flight where departure_airport = %s and arrival_airport = %s'
                cursor.execute(query, (departure_airport, arrival_airport))
                flights += cursor.fetchall()
    cursor.close()
    return render_template('search_result_login.html', flights=flights, error=error)


# Generate the home page for a customer
@app.route('/home_customer')
def home_customer():
    username = session['username']
    email = session['email']
    date_today = datetime.today()

    # search for the upcoming flights and show it on the home page
    cursor = conn.cursor()
    query = 'select * from flight natural join ticket natural join purchases ' \
            'where customer_email = %s and departure_time > %s'
    cursor.execute(query, (email, date_today - timedelta(days=1)))
    flights = cursor.fetchall()
    cursor.close()

    # get the total spending in the past year, and show it on the home page
    date_last_year = str(date_today - timedelta(days=365))
    cursor = conn.cursor()
    query = 'select sum(price) as total from flight natural join ticket natural join purchases ' \
            'where customer_email = %s and purchase_date > %s'
    cursor.execute(query, (email, date_last_year))
    spending = cursor.fetchall()
    cursor.close()

    # a bar chart showing month wise money spent for last 6 months
    labels = []
    values = []
    get_month = date_today
    for i in range(6):
        cursor = conn.cursor()
        query = 'select sum(price) as total from flight natural join ticket natural join purchases ' \
                'where customer_email = %s and YEAR(purchase_date) = %s and MONTH(purchase_date) = %s'
        cursor.execute(query, (email, str(get_month.year), str(get_month.month)))
        monthly_spending = cursor.fetchone()
        monthly_spending = monthly_spending['total']
        cursor.close()
        labels.append(get_month.strftime("%Y-%m"))
        if monthly_spending:
            values.append(monthly_spending)
        else:
            values.append(0)
        get_month -= relativedelta(months=1)

    return render_template('home_customer.html', username=username, flights=flights, spending=spending,
                               labels=labels[::-1], values=values[::-1])


# Generate the home page for an airline staff
@app.route('/home_staff')
def home_staff():
    username = session['username']
    airline = session['airline']

    date_today = datetime.today()
    date_in_a_month = str(date_today + timedelta(days=30))

    # search for the upcoming flights and show it on the home page
    cursor = conn.cursor()
    query = 'select * from flight where airline_name = %s ' \
            'and departure_time > %s and departure_time < %s'
    cursor.execute(query, (airline, date_today - timedelta(days=1), date_in_a_month))
    flights = cursor.fetchall()
    cursor.close()

    # view top 5 booking agents based on number of ticket sales for the past month
    date_last_month = str(date_today - timedelta(days=30))
    cursor = conn.cursor()
    query = 'select booking_agent_id, count(*) as number ' \
            'from ticket natural join purchases ' \
            'where airline_name=%s and purchase_date > %s and booking_agent_id is not null ' \
            'group by booking_agent_id order by number limit 5'
    cursor.execute(query, (airline, date_last_month))
    agent_count_month = cursor.fetchall()
    cursor.close()

    # view top 5 booking agents based on number of ticket sales for the past year
    date_last_year = str(date_today - timedelta(days=365))
    cursor = conn.cursor()
    query = 'select booking_agent_id, count(*) as number ' \
            'from ticket natural join purchases ' \
            'where airline_name=%s and purchase_date > %s and booking_agent_id is not null ' \
            'group by booking_agent_id order by number limit 5'
    cursor.execute(query, (airline, date_last_year))
    agent_count_year = cursor.fetchall()
    cursor.close()

    # view top 5 booking agents based on the amount of commission received for the past year
    cursor = conn.cursor()
    query = 'select booking_agent_id, 0.1 * sum(price) as commission ' \
            'from ticket natural join purchases natural join flight ' \
            'where airline_name=%s and purchase_date > %s and booking_agent_id is not null ' \
            'group by booking_agent_id order by commission limit 5'
    cursor.execute(query, (airline, date_last_year))
    commission = cursor.fetchall()
    cursor.close()

    # see the most frequent customer within tha last year
    cursor = conn.cursor()
    query = 'select customer_email, count(*) as number ' \
            'from ticket natural join purchases ' \
            'where airline_name=%s and purchase_date > %s ' \
            'group by customer_email order by number limit 5'
    cursor.execute(query, (airline, date_last_year))
    most_freq_customer = cursor.fetchall()
    cursor.close()

    # view total amount of tickets sold last year
    cursor = conn.cursor()
    query = 'select count(*) as number from ticket natural join purchases ' \
            'where airline_name = %s and purchase_date > %s'
    cursor.execute(query, (airline, date_last_year))
    tickets_last_year = cursor.fetchone()['number']
    cursor.close()

    # view total amount of tickets sold last month
    cursor = conn.cursor()
    query = 'select count(*) as number from ticket natural join purchases ' \
            'where airline_name = %s and purchase_date > %s'
    cursor.execute(query, (airline, date_last_month))
    tickets_last_month = cursor.fetchone()['number']
    cursor.close()

    # a bar chart showing month wise money spent for last 6 months
    labels = []
    values = []
    get_month = date_today
    for i in range(6):
        cursor = conn.cursor()
        query = 'select count(*) as number from ticket natural join purchases ' \
                'where airline_name = %s and YEAR(purchase_date) = %s and MONTH(purchase_date) = %s'
        cursor.execute(query, (airline, str(get_month.year), str(get_month.month)))
        monthly_sold = cursor.fetchone()
        monthly_sold = monthly_sold['number']
        cursor.close()
        labels.append(get_month.strftime("%Y-%m"))
        if monthly_sold:
            values.append(monthly_sold)
        else:
            values.append(0)
        get_month -= relativedelta(months=1)

    # a pie chart showing total amount of revenue earned from direct sales
    # and total amount of revenue earned from indirect sales in the last year
    labels_pie = ["direct", "indirect"]
    values_pie_year = []
    values_pie_month = []
    colors = ["#F7464A", "#46BFBD"]

    cursor = conn.cursor()
    query = 'select sum(price) as revenue from flight natural join ticket natural join purchases ' \
            'where airline_name = %s and purchase_date > %s and booking_agent_id is null '
    cursor.execute(query, (airline, date_last_year))
    revenue = cursor.fetchone()['revenue']
    values_pie_year.append(revenue)

    query = 'select sum(price) as revenue from flight natural join ticket natural join purchases ' \
            'where airline_name = %s and purchase_date > %s and booking_agent_id is not null '
    cursor.execute(query, (airline, date_last_year))
    revenue = cursor.fetchone()['revenue']
    values_pie_year.append(revenue)
    cursor.close()

    # a pie chart showing total amount of revenue earned from direct sales
    # and total amount of revenue earned from indirect sales in the last month
    cursor = conn.cursor()
    query = 'select sum(price) as revenue from flight natural join ticket natural join purchases ' \
            'where airline_name = %s and purchase_date > %s and booking_agent_id is null '
    cursor.execute(query, (airline, date_last_month))
    revenue = cursor.fetchone()['revenue']
    values_pie_month.append(revenue)

    query = 'select sum(price) as revenue from flight natural join ticket natural join purchases ' \
            'where airline_name = %s and purchase_date > %s and booking_agent_id is not null '
    cursor.execute(query, (airline, date_last_month))
    revenue = cursor.fetchone()['revenue']
    values_pie_month.append(revenue)
    cursor.close()

    # find the top 3 destinations for last 3 months
    date_3month_ago = str(date_today - relativedelta(months=3))
    cursor = conn.cursor()
    query = 'select airport_city, count(*) as visits ' \
            'from ticket natural join flight, airport ' \
            'where flight.arrival_airport = airport.airport_name and airline_name=%s ' \
            'and departure_time > %s and departure_time < %s ' \
            'group by airport_city order by visits limit 3'
    cursor.execute(query, (airline, date_3month_ago, str(date_today)))
    top_destinations_3M = cursor.fetchall()
    cursor.close()

    # find the top 3 destinations for last year
    cursor = conn.cursor()
    query = 'select airport_city, count(*) as visits ' \
            'from ticket natural join flight, airport ' \
            'where flight.arrival_airport = airport.airport_name and airline_name=%s ' \
            'and departure_time > %s and departure_time < %s ' \
            'group by airport_city order by visits limit 3'
    cursor.execute(query, (airline, date_last_year, str(date_today)))
    top_destinations = cursor.fetchall()
    cursor.close()

    return render_template('home_staff.html', username=username, flights=flights, agent_count_month=agent_count_month,
                           agent_count_year=agent_count_year, commission=commission,
                           most_freq_customer=most_freq_customer, top_destinations=top_destinations,
                           top_destinations_3M=top_destinations_3M, labels=labels, values=values,
                           tickets_last_year=tickets_last_year, tickets_last_month=tickets_last_month,
                           set=zip(labels_pie, values_pie_year, colors),
                           set_month=zip(labels_pie, values_pie_month, colors))


# Generate the home page for a booking agent
@app.route('/home_agent')
def home_agent():
    email = session['email']
    agent_id = session['id']
    date_today = datetime.today()

    # search for the upcoming flights and show it on the home page
    cursor = conn.cursor()
    query = 'select * from flight natural join ticket natural join purchases ' \
            'where booking_agent_id = %s and departure_time > %s'
    cursor.execute(query, (agent_id, date_today - timedelta(days=1)))
    flights = cursor.fetchall()
    cursor.close()

    date_last_month = str(date_today - timedelta(days=30))

    cursor = conn.cursor()
    query = 'select 0.1 * sum(price) as commission ' \
            'from ticket natural join purchases natural join flight ' \
            'where booking_agent_id=%s and purchase_date > %s'
    cursor.execute(query, (agent_id, date_last_month))
    total_commission = cursor.fetchone()['commission']
    # make sure there is value in total commission
    if not total_commission:
        total_commission = 0
    cursor.close()

    cursor = conn.cursor()
    query = 'select count(*) as number ' \
            'from ticket natural join purchases natural join flight ' \
            'where booking_agent_id=%s and purchase_date > %s'
    cursor.execute(query, (agent_id, date_last_month))
    total_tickets = cursor.fetchone()['number']
    cursor.close()

    # make sure the agent had bought tickets
    avg_commission = ''
    if total_tickets > 0:
        avg_commission = '%.2f' % (total_commission/total_tickets)

    date_6month_ago = str(date_today - relativedelta(months=6))
    cursor = conn.cursor()
    query = 'select customer_email, count(*) as tickets ' \
            'from purchases where booking_agent_id=%s and purchase_date > %s ' \
            'group by customer_email order by tickets desc limit 5'
    cursor.execute(query, (agent_id, date_6month_ago))
    top_customers = cursor.fetchall()
    labels_1 = []
    values_1 = []
    for item in top_customers:
        labels_1.append(item['customer_email'])
        values_1.append(item['tickets'])

    date_last_year = str(date_today - timedelta(days=365))
    cursor = conn.cursor()
    query = 'select customer_email, 0.1 * sum(price) as tickets ' \
            'from purchases natural join ticket natural join flight ' \
            'where booking_agent_id=%s and purchase_date > %s ' \
            'group by customer_email order by tickets desc limit 5'
    cursor.execute(query, (agent_id, date_last_year))
    top_customers = cursor.fetchall()
    labels_2 = []
    values_2 = []
    for item in top_customers:
        labels_2.append(item['customer_email'])
        values_2.append(item['tickets'])
    cursor.close()

    return render_template('home_agent.html', id=agent_id, flights=flights, total_commission=total_commission,
                           total_tickets=total_tickets, avg_commission=avg_commission, labels_1=labels_1,
                           values_1=values_1, labels_2=labels_2, values_2=values_2)


# Logout from a customer session
@app.route('/logout_c')
def logout1():
    session.pop('username')
    return redirect('/')


# Logout from a booking agent session
@app.route('/logout_a')
def logout2():
    session.pop('id')
    return redirect('/')


# Logout from a customer session
@app.route('/logout_s')
def logout3():
    session.pop('airline')
    return redirect('/')


# Define route for login
@app.route('/login')
def login():
    return render_template('login.html')


# Define route for register as a customer
@app.route('/register_c')
def register_c():
    return render_template('register_c.html')


# Define route for register as a booking agent
@app.route('/register_a')
def register_a():
    return render_template('register_a.html')


# Define route for register as an airline staff
@app.route('/register_s')
def register_s():
    return render_template('register_s.html')


# Define route for the search result page without login
@app.route('/search1')
def search1():
    return render_template('search1.html')


# Define route for the search result page after login
@app.route('/search2')
def search2():
    return render_template('search2.html')


# Parse the purchase request
@app.route('/purchase', methods=["POST"])
def purchase():
    status = 'Succeed!'
    airline_name = request.form['airline_name']
    flight_number = request.form['flight_number']
    customer_email = request.form['customer_email']
    date = request.form['date']

    email = session['email']
    agent_id = session['id']

    cursor = conn.cursor()
    if agent_check(agent_id):
        query1 = 'select count(*) from flight natural join ticket natural join airplane where airline_name = %s and flight_num = %s'
        cursor.execute(query1, (airline_name, flight_number))
        value1 = cursor.fetchall()

        query2 = 'select seats from airplane natural join flight where airline_name = %s and flight_num = %s'
        cursor.execute(query2, (airline_name, flight_number))
        value2 = cursor.fetchall()

        if value1[0]['count(*)'] < value2[0]['seats']:
            query3 = 'select max(ticket_id) from ticket where airline_name = %s and flight_num = %s'
            cursor.execute(query3, (airline_name, flight_number))

            value3 = cursor.fetchall()
            max_ticket = value3[0]['max(ticket_id)']

            # see if there exists a ticket; if not, create the initial one.
            if max_ticket:
                ticket_no = max_ticket + 1
            else:
                ticket_no = int(flight_number) * 1000 + 1

            # create a new ticket
            query4 = 'INSERT INTO ticket VALUES(%s, %s, %s)'
            cursor.execute(query4, (ticket_no, airline_name, flight_number))

            # purchase the ticket for the customer
            query5 = 'INSERT INTO purchases VALUES(%s, %s, %s, %s)'
            cursor.execute(query5, (ticket_no, customer_email, agent_id, date))

        else:
            status = 'The flight is full!'

        conn.commit()
        cursor.close()
        return render_template('agent_feedback.html', status=status)
    elif email == customer_email:  # user is customer
        query1 = 'select count(*) from flight natural join ticket natural join airplane where airline_name = %s and flight_num = %s'
        cursor.execute(query1, (airline_name, flight_number))
        value1 = cursor.fetchall()

        query2 = 'select seats from airplane natural join flight where airline_name = %s and flight_num = %s'
        cursor.execute(query2, (airline_name, flight_number))
        value2 = cursor.fetchall()

        if value1[0]['count(*)'] < value2[0]['seats']:
            query3 = 'select max(ticket_id) from ticket where airline_name = %s and flight_num = %s'
            cursor.execute(query3, (airline_name, flight_number))
            value3 = cursor.fetchall()
            max_ticket = value3[0]['max(ticket_id)']
            # see if there exists a ticket; if not, create the initial one.
            if max_ticket:
                ticket_no = max_ticket + 1
            else:
                ticket_no = int(flight_number) * 1000 + 1

            # create a new ticket
            query4 = 'INSERT INTO ticket VALUES(%s, %s, %s)'
            cursor.execute(query4, (ticket_no, airline_name, flight_number))

            # purchase the ticket for the customer
            query5 = 'insert into purchases values(%s, %s, %s, %s)'
            cursor.execute(query5, (ticket_no, customer_email, None, date))
        else:
            status = "The flight is full!"

        conn.commit()
        cursor.close()
        return render_template('customer_feedback.html', status=status)
    else:
        if agent_id:  # CANNOT HAPPEN
            status = "Please purchase ticket for the correct customer."
            return render_template('agent_feedback.html', status=status)
        else:
            status = "Please only purchase ticket for yourself."
            return render_template('customer_feedback.html', status=status)


###################################
# Staff functions

# Check the session status before allowing the staff to change the database
def security_check(airline, user):
    cursor = conn.cursor()
    query = 'select * from airline_staff where username = %s and airline_name = %s'
    cursor.execute(query, (user, airline))
    flag = cursor.fetchall()
    cursor.close()
    if flag:
        return True
    else:
        return False


# For airline staff to view all the flights of his/her airline within a range
@app.route('/staff_view_flights', methods=['GET', 'POST'])
def staff_view_flights():
    status = "Succeed!"
    airline = session['airline']
    username = session['username']
    flights = []

    if security_check(airline, username):
        source = request.form['departure_airport']
        departure_time = request.form['departure_time']
        arrival_time = request.form['arrival_time']
        arrival = request.form['arrival_airport']

        source = get_airport(source)
        arrival = get_airport(arrival)
        flights = []
        cursor = conn.cursor()

        print(source)
        print(arrival)

        for departure_airport in source:
            for arrival_airport in arrival:
                query = 'select * from flight where airline_name = %s and departure_airport = %s and ' \
                        'departure_time > %s and arrival_time < %s and arrival_airport = %s'
                cursor.execute(query, (airline, departure_airport, departure_time, arrival_time, arrival_airport))
                flights += cursor.fetchall()
        cursor.close()
    else:
        status = "Failed!"
    return render_template('staff_view_flights.html', flights=flights, status=status)


# For airline staff to view a particular customer's all flights of the airline
@app.route('/customer_flights', methods=['GET', 'POST'])
def customer_flights():
    status = "Succeed!"
    # grabs information from the forms
    airline = session['airline']
    username = session['username']
    flights = []

    if security_check(airline, username):
        customer_email = request.form['customer_email']
        cursor = conn.cursor()
        query = 'select * from flight natural join ticket natural join purchases where airline_name=%s and customer_email = %s'
        cursor.execute(query, (airline, customer_email))
        flights = cursor.fetchall()
        cursor.close()
    else:
        status = 'Failed!'
    return render_template('staff_cusFlights.html', flights=flights, status=status, username=username)


# For airline staff to create new flights
@app.route('/create_flights', methods=['GET', 'POST'])
def create_flights():
    status = 'Succeed!'
    airline = session['airline']
    username = session['username']

    if security_check(airline, username):
        flight_num = int(request.form['flight_number'])
        departure_airport = request.form['departure_airport']
        departure_time = request.form['departure_time']
        arrival_airport = request.form['arrival_airport']
        arrival_time = request.form['arrival_time']
        price = int(request.form['price'])
        status = request.form['status']
        airplane_id = int(request.form['airplane_id'])

        # find out if the flight exists
        query0 = 'select * from flight where flight_num = %s'
        cursor.execute(query0, flight_num)
        r = cursor.fetchall()
        if r:  # there is already a flight with the same flight number in the system
            status = "There is already a flight with the same flight number in the system!"
            return render_template('staff_feedback.html', status=status)

        # find out if airport exists
        q0 = 'select * from airport where airport_name = %s'
        cursor.execute(q0, departure_airport)
        r0 = cursor.fetchall()
        cursor.execute(q0, arrival_airport)
        r1 = cursor.fetchall()
        if not r0 or not r1:
            status = "Please enter existing airports!"
            return render_template('staff_feedback.html', status=status)

        # find out if airplane id belongs to this airline
        q2 = 'select * from airplane where airline_name = %s and airplane_id = %s'
        cursor.execute(q2, (airline, airplane_id))
        r2 = cursor.fetchall()
        if not r2:  # airplane does not belong to this airline
            status = "Please make sure that your airline owns this airplane!"
            return render_template('staff_feedback.html', status=status)

        query = 'insert into flight values(%s, %s, %s, %s, %s, %s, %s, %s, %s)'
        cursor.execute(query, (airline, flight_num, departure_airport, departure_time, arrival_airport, arrival_time, price, status, airplane_id))
        conn.commit()
        cursor.close()
    else:
        status = "Failed!"
    return render_template('staff_feedback.html', status=status)


# For airline staff to change the status of a selected flight
@app.route('/change_status', methods=['GET', 'POST'])
def change_status():
    status = 'Succeed!'
    airline = session['airline']
    username = session['username']

    if security_check(airline, username):
        flight_num = request.form['flight_number']
        departure_time = request.form['departure_time']
        update = request.form['status']
        cursor = conn.cursor()

        # find out if the flight exists
        query0 = 'select * from flight where flight_num = %s and date(departure_time) = %s'
        cursor.execute(query0, (flight_num, departure_time))
        r = cursor.fetchall()
        if not r:  # no such flight
            status = "Please double check your input; it does not match with our record."
            return render_template('staff_feedback.html', status=status)

        query = 'update flight set status = %s where airline_name = %s and ' \
                'flight_num = %s and departure_time = %s'
        cursor.execute(query, (update, airline, flight_num, departure_time))
        conn.commit()
        cursor.close()
    else:
        status = 'Failed!'
    return render_template('staff_feedback.html', status=status, username=username)


# For airline staff to add a new airplane in their system
@app.route('/add_airplane', methods=['GET', 'POST'])
def add_airplane():
    status = "Succeed!"
    airline = session['airline']
    username = session['username']

    if security_check(airline, username):
        airplane_id = int(request.form['airplane_id'])
        seats = int(request.form['seats'])
        cursor = conn.cursor()

        # find out if the airplane already exists
        query0 = 'select * from airplane where airplane_id = %s'
        cursor.execute(query0, airplane_id)
        r = cursor.fetchall()
        if r:  # there is already a flight with the same flight number in the system
            status = "There is already an airplane with the same ID in the system!"
            return render_template('staff_feedback.html', status=status, username=username)

        query = 'insert into airplane values(%s, %s, %s)'
        cursor.execute(query, (airline, airplane_id, seats))
        conn.commit()
        cursor.close()
    else:
        status = 'Failed!'
    return render_template('staff_feedback.html', status=status, username=username)


# For airline staff to add a new airport in their system
@app.route('/add_airport', methods=['GET', 'POST'])
def add_airport():
    status = 'Succeed!'
    airline = session['airline']
    username = session['username']
    if security_check(airline, username):
        airport_name = request.form['airport_name']
        airport_city = request.form['airport_city']
        cursor = conn.cursor()

        # find out if the airport already exists
        query0 = 'select * from airport where airport_name = %s'
        cursor.execute(query0, airport_name)
        r = cursor.fetchall()
        if r:  # there is already an airport with the same ID in the system
            status = "There is already an airport with the same ID in the system!"
            return render_template('home_staff.html', status=status, username=username)

        query = 'insert into airport values(%s, %s)'
        cursor.execute(query, (airport_name, airport_city))
        conn.commit()
        cursor.close()
    else:
        status = 'Failed!'
    return render_template('staff_feedback.html', status=status, username=username)


# For airline staff to view the report of tickets sold within a range
@app.route('/view_report', methods=['GET', "POST"])
def view_report():
    status = 'Succeed!'
    airline = session['airline']
    username = session['username']
    total = 0
    labels = []
    values = []

    if security_check(airline, username):
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        # view total amount of tickets sold based on the range
        cursor = conn.cursor()
        query = 'select count(*) as number from ticket natural join purchases ' \
                'where airline_name = %s and purchase_date > %s and purchase_date < %s'
        cursor.execute(query, (airline, start_date, end_date))
        total = cursor.fetchone()['number']
        cursor.close()

        # a bar chart showing month wise money spent for last 6 months
        labels = []
        values = []
        get_month = datetime.strptime(end_date, '%Y-%m-%d')
        while get_month > datetime.strptime(start_date, '%Y-%m-%d'):
            cursor = conn.cursor()
            query = 'select count(*) as number from ticket natural join purchases ' \
                    'where airline_name = %s and YEAR(purchase_date) = %s and MONTH(purchase_date) = %s'
            cursor.execute(query, (airline, str(get_month.year), str(get_month.month)))
            monthly_sold = cursor.fetchone()
            monthly_sold = monthly_sold['number']
            cursor.close()
            labels.append(get_month.strftime("%Y-%m"))
            if monthly_sold:
                values.append(monthly_sold)
            else:
                values.append(0)
            get_month -= relativedelta(months=1)
    else:
        status = 'Failed!'

    return render_template('airline_report.html', status=status, total=total, labels=labels,
                           values=values, username=username)


###################################
# Agent functions

# Check the session status before allowing the booking agent to search
def agent_check(id):
    # if no id, return false
    if not id:
        return False
    else:
        cursor = conn.cursor()
        query = 'select * from booking_agent where booking_agent_id = %s'
        cursor.execute(query, id)
        flag = cursor.fetchall()
        cursor.close()
        if flag:
            return True
        else:
            return False


# For booking agent to view all the flights he/her purchased on behalf of customers
@app.route('/agent_view_flights', methods=['GET', 'POST'])
def agent_view_flights():
    status = 'Succeed!'
    flights = []
    agent_id = session['id']
    if agent_check(agent_id):
        source = request.form['departure_airport']
        departure_time = request.form['departure_time']
        arrival_time = request.form['arrival_time']
        arrival = request.form['arrival_airport']

        source = get_airport(source)
        arrival = get_airport(arrival)
        flights = []
        cursor = conn.cursor()

        for departure_airport in source:
            for arrival_airport in arrival:
                query = 'select * from flight natural join ticket natural join purchases ' \
                        'where booking_agent_id = %s and departure_airport = %s and ' \
                        'departure_time > %s and arrival_time < %s and arrival_airport = %s'
                cursor.execute(query, (agent_id, departure_airport, departure_time, arrival_time, arrival_airport))
                flights += cursor.fetchall()
        cursor.close()
    else:
        status = 'Failed!'
    return render_template('agent_view_flights.html', flights=flights, status=status)


# For booking agent to view the commission he/she received within a range
@app.route('/view_commission', methods=['GET', 'POST'])
def view_commission():
    status = 'Succeed!'
    commission = 0
    tickets = 0
    agent_id = session['id']

    if agent_check(agent_id):
        start_time = request.form['start_time']
        end_time = request.form['end_time']

        cursor = conn.cursor()
        query = 'select 0.1 * sum(price) as commission ' \
                'from ticket natural join purchases natural join flight ' \
                'where booking_agent_id=%s and purchase_date > %s and purchase_date < %s'
        cursor.execute(query, (agent_id, start_time, end_time))
        commission = cursor.fetchone()['commission']
        cursor.close()

        cursor = conn.cursor()
        query = 'select count(*) as number ' \
                'from ticket natural join purchases natural join flight ' \
                'where booking_agent_id=%s and purchase_date > %s and purchase_date < %s'
        cursor.execute(query, (agent_id, start_time, end_time))
        tickets = cursor.fetchone()['number']
        cursor.close()
    else:
        status = 'Failed!'

    return render_template('view_commission.html', status=status, commission=commission, tickets=tickets)


###################################
# Customer functions

# Check the session status before allowing the customer to search
def customer_check(email):
    # if no id, return false
    if not id:
        return False
    else:
        cursor = conn.cursor()
        query = 'select * from customer where email = %s'
        cursor.execute(query, email)
        flag = cursor.fetchall()
        cursor.close()
        if flag:
            return True
        else:
            return False


# For customer to view all his/her flights within a range
@app.route('/customer_view_flights', methods=['GET', 'POST'])
def customer_view_flights():
    status = 'Succeed!'
    email = session['email']
    flights = []
    if customer_check(email):
        source = request.form['departure_airport']
        departure_time = request.form['departure_time']
        arrival_time = request.form['arrival_time']
        arrival = request.form['arrival_airport']

        source = get_airport(source)
        arrival = get_airport(arrival)
        flights = []
        cursor = conn.cursor()

        for departure_airport in source:
            for arrival_airport in arrival:
                query = 'select * from flight natural join ticket natural join purchases ' \
                        'where customer_email = %s and departure_airport = %s and ' \
                        'departure_time > %s and arrival_time < %s and arrival_airport = %s'
                cursor.execute(query, (email, departure_airport, departure_time, arrival_time, arrival_airport))
                flights += cursor.fetchall()
        cursor.close()
    else:
        status = 'Failed!'

    return render_template('customer_view_flights.html', status=status, flights=flights)


# For customer to view his/her spending within a range
@app.route('/view_spending', methods=['GET', "POST"])
def view_spending():
    status = 'Succeed!'
    spending = 0
    labels = []
    values = []
    email = session['email']

    if customer_check(email):
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        # view total amount of spending based on the range
        cursor = conn.cursor()
        query = 'select sum(price) as spending from ticket natural join purchases natural join flight ' \
                'where customer_email = %s and purchase_date > %s and purchase_date < %s'
        cursor.execute(query, (email, start_date, end_date))
        spending = cursor.fetchone()['spending']
        cursor.close()

        # a bar chart showing month wise money spent for last 6 months
        labels = []
        values = []
        get_month = datetime.strptime(end_date, '%Y-%m-%d')
        while get_month > datetime.strptime(start_date, '%Y-%m-%d'):
            cursor = conn.cursor()
            query = 'select sum(price) as spending from ticket natural join purchases natural join flight ' \
                    'where customer_email = %s and YEAR(purchase_date) = %s and MONTH(purchase_date) = %s'
            cursor.execute(query, (email, str(get_month.year), str(get_month.month)))
            monthly_cost = cursor.fetchone()
            monthly_cost = monthly_cost['spending']
            cursor.close()
            labels.append(get_month.strftime("%Y-%m"))
            if monthly_cost:
                values.append(monthly_cost)
            else:
                values.append(0)
            get_month -= relativedelta(months=1)
    else:
        status = 'Failed!'

    return render_template('customer_spending.html', status=status, spending=spending, labels=labels, values=values)

###################################


if __name__ == '__main__':
    app.run()


