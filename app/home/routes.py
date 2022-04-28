import os

from functools import wraps
from flask import redirect, render_template, session, jsonify, request, g
from . import home
from decouple import config
import pymysql

def connect_db():
    db_conn = pymysql.connect(
        db       = config('DB_NAME'),
        host     = config('DB_HOST'),
        port     = int(config('DB_PORT')),
        user     = config('DB_USER'),
        password = config('DB_PASS'),
    )

    return db_conn

def get_db():
    '''Opens a new database connection per request.'''
    if not hasattr(g, 'db'):
        g.db = connect_db()
        # db_cursor.execute('set global max_allowed_packet=67108864') # 1048576000

    return g.db

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'profile' not in session:
            return redirect('/login')
        return f(*args, **kwargs)

    return decorated

@home.route('/dashboard', methods=['GET'])
@requires_auth
def index():

    states = []
    regions = []
    competitors = []
    stores = []

    try:
        states_sql = "SELECT DISTINCT location_state, location_designation FROM umbric.locations_home"
        db_cursor = get_db().cursor()
        db_cursor.execute(states_sql)
        state_rows = db_cursor.fetchall()
        states = [state[0] for state in list(state_rows)]
        states = list(set(states))
        states.sort()

        stores = [state[1] for state in list(state_rows)]
        stores.sort()

        distance_sql = "SELECT DISTINCT location_market, location_market_owner FROM umbric.locations_distances"
        db_cursor.execute(distance_sql)
        distance_rows = db_cursor.fetchall()
        regions = [distance[0] for distance in list(distance_rows) if distance[0] is not None]
        managers = [distance[1] for distance in list(distance_rows) if distance[1] is not None]
        regions.sort()
        managers = list(dict.fromkeys(managers))
        managers.sort()

        competitors_sql = "SELECT DISTINCT(location_franchise) FROM umbric.locations_jiffy"
        db_cursor.execute(competitors_sql)
        competitor_rows = db_cursor.fetchall()
        competitors = [competitor[0] for competitor in list(competitor_rows)]

        # states = ['AL', 'AR', 'AZ', 'CA', 'CO', 'CT', 'FL', 'GA', 'IA', 'ID', 'IL', 'IN', 'KY', 'LA']
        # regions = ['11', '12', '31', '33', '32', '35', '34', '42', '25', '26', '59', '50', '55', '51']
        # locations = ['1783 North Crossover Rd, Fayetteville AR 72701', '1730 West Bell Rd, Phoenix AZ 85023']
        # competitors = ['jiffy']

        print("processed get request...")

    except Exception as e:
        print(e)

    return render_template(
        'home/index.html',
        states=states,
        regions=regions,
        competitors=competitors,
        stores=stores,
        managers=managers
    )

@home.route('/search', methods=['POST'])
def search():
    try:
        form_data = request.form.to_dict()
        if not form_data.get('location'):
            raise Exception('Location could not found')

        competitor = form_data.get('competitor')

        location_sql = f"SELECT location_destination, location_distance  FROM umbric.locations_distances WHERE location_origin = '{form_data.get('location')}'"
        db_cursor = get_db().cursor()
        db_cursor.execute(location_sql)
        location_rows = db_cursor.fetchall()

        coupons = []
        coupon_columns = ['coupon_text', 'coupon_service', 'coupon_lastseen', 'coupon_category', 'coupon_type', 'location_key', 'competitor', 'location_phone']
        for location in list(location_rows):
            coupon_sql = f"SELECT DISTINCT c.coupon_text, c.coupon_service, c.coupon_lastseen, c.coupon_category, c.coupon_type, c.location_key, j.location_franchise, j.location_phone FROM umbric.locations_coupons c JOIN umbric.locations_jiffy j ON c.location_destination = j.location_address WHERE location_destination = '{location[0]}'"

            if competitor:
                coupon_sql += f" AND j.location_franchise = '{competitor}'"

            db_cursor.execute(coupon_sql)
            coupon_rows = db_cursor.fetchall()

            data = [dict(zip(coupon_columns, row)) for row in list(coupon_rows)]

            for d in data:
                try:
                    d['coupon_lastseen'] = d['coupon_lastseen'].isoformat()
                    d['destination'] = location[0]
                    d['distance'] = location[1]
                    d['note'] = f"{d['coupon_text']} {d['coupon_service']} ({'{:.1f}'.format(d['distance'])}m - {d['competitor']} @ {d['destination'].split(',')[0]} - {d['location_phone']})"
                except:
                    continue

            coupons.extend(data)

        return jsonify({
            "success": True,
            "data": coupons,
        })

    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 400


@home.route('/market_search', methods=['POST'])
def market_search():
    try:
        form_data = request.form.to_dict()
        market = form_data.get('market')
        if not market:
            raise Exception('Market could not found')

        coupon_columns = ['coupon_text', 'coupon_service', 'coupon_lastseen', 'coupon_category', 'coupon_type', 'destination', 'location_key', 'competitor', 'location_phone', 'distance']

        coupon_sql = f"SELECT DISTINCT c.coupon_text, c.coupon_service, c.coupon_lastseen, c.coupon_category, c.coupon_type, c.location_destination, c.location_key, j.location_franchise, j.location_phone, d.location_distance FROM umbric.locations_coupons c JOIN umbric.locations_jiffy j ON c.location_destination = j.location_address JOIN umbric.locations_distances d ON c.location_destination = d.location_destination WHERE c.location_market  = '{market}'"
        db_cursor = get_db().cursor()
        db_cursor.execute(coupon_sql)
        coupon_rows = db_cursor.fetchall()

        data = [dict(zip(coupon_columns, row)) for row in list(coupon_rows)]

        for d in data:
            try:
                d['coupon_lastseen'] = d['coupon_lastseen'].isoformat()
                d['note'] = f"{d['coupon_text']} {d['coupon_service']} ({'{:.1f}'.format(float(d['distance']))}m - {d['competitor']} @ {d['destination'].split(',')[0]} - {d['location_phone']})"
            except Exception as e:
                print(e)
                continue

        # Close db connection
        # db_conn.close()

        return jsonify({
            "success": True,
            "data": data,
        })

    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 400


@home.route('/managers_search', methods=['POST'])
def managers_search():
    try:
        form_data = request.form.to_dict()
        manager = form_data.get('manager')
        if not manager:
            raise Exception('Manager could not found')

        coupon_columns = ['coupon_text', 'coupon_service', 'coupon_lastseen', 'coupon_category', 'coupon_type', 'destination', 'location_key', 'competitor', 'location_phone', 'distance']

        coupon_sql = f"SELECT DISTINCT c.coupon_text, c.coupon_service, c.coupon_lastseen, c.coupon_category, c.coupon_type, c.location_destination, c.location_key, j.location_franchise, j.location_phone, d.location_distance FROM umbric.locations_coupons c JOIN umbric.locations_jiffy j ON c.location_destination = j.location_address JOIN umbric.locations_distances d ON c.location_destination = d.location_destination WHERE d.location_market_owner = '{manager}'"
        db_cursor = get_db().cursor()
        db_cursor.execute(coupon_sql)
        coupon_rows = db_cursor.fetchall()

        data = [dict(zip(coupon_columns, row)) for row in list(coupon_rows)]

        for d in data:
            try:
                d['coupon_lastseen'] = d['coupon_lastseen'].isoformat()
                d['note'] = f"{d['coupon_text']} {d['coupon_service']} ({'{:.1f}'.format(float(d['distance']))}m - {d['competitor']} @ {d['destination'].split(',')[0]} - {d['location_phone']})"
            except Exception as e:
                print(e)
                continue

        # Close db connection
        # db_conn.close()

        return jsonify({
            "success": True,
            "data": data,
        })

    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 400


@home.route('/location_search', methods=['POST'])
def location_search():
    try:
        form_data = request.form.to_dict()
        state = form_data.get('state')
        if not state:
            raise Exception('State could not found')

        # distance_sql = f"SELECT DISTINCT location_origin FROM umbric.locations_distances WHERE location_origin REGEXP '.*[[:blank:]]+{state}[[:blank:]]+[0-9]{{5}}$'"
        # db_cursor.execute(distance_sql)
        # distance_rows = db_cursor.fetchall()
        # locations = [distance[0] for distance in list(distance_rows) if distance[0] is not None]

        number_columns = ['address', 'number']
        numbers_sql = f"SELECT DISTINCT location_address, location_designation FROM umbric.locations_home WHERE location_state = '{state}'"
        db_cursor = get_db().cursor()
        db_cursor.execute(numbers_sql)
        numbers_rows = db_cursor.fetchall()
        locations = [dict(zip(number_columns, row)) for row in list(numbers_rows)]

        return jsonify({
            "success": True,
            "data": locations,
            # "numbers": numbers,
        })

    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 400


@home.route('/store_search', methods=['POST'])
def store_search():
    try:
        form_data = request.form.to_dict()
        store = form_data.get('store')
        competitor = form_data.get('competitor')

        if not store:
            raise Exception('Store could not found')

        coupon_columns = ['coupon_text', 'coupon_service', 'coupon_lastseen', 'coupon_category', 'coupon_type', 'destination', 'location_key', 'competitor', 'location_phone', 'distance']

        coupon_sql = f"SELECT DISTINCT c.coupon_text, c.coupon_service, c.coupon_lastseen, c.coupon_category, c.coupon_type, c.location_destination, c.location_key, j.location_franchise, j.location_phone, d.location_distance FROM umbric.locations_coupons c JOIN umbric.locations_jiffy j ON c.location_destination = j.location_address JOIN umbric.locations_distances d ON c.location_destination = d.location_destination JOIN umbric.locations_home h ON d.location_origin = h.location_address WHERE h.location_designation  = '{store}'"

        if competitor:
            coupon_sql += f" AND j.location_franchise = '{competitor}'"

        db_cursor = get_db().cursor()
        db_cursor.execute(coupon_sql)
        coupon_rows = db_cursor.fetchall()

        data = [dict(zip(coupon_columns, row)) for row in list(coupon_rows)]

        for d in data:
            try:
                d['coupon_lastseen'] = d['coupon_lastseen'].isoformat()
                d['note'] = f"{d['coupon_text']} {d['coupon_service']} ({'{:.1f}'.format(float(d['distance']))}m - {d['competitor']} @ {d['destination'].split(',')[0]} - {d['location_phone']})"
            except Exception as e:
                print(e)
                continue

        # Close db connection
        # db_conn.close()

        return jsonify({
            "success": True,
            "data": data,
        })

    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 400
