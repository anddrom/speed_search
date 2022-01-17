import os

from flask import request, render_template, jsonify
from . import home

import pymysql

db_conn = pymysql.connect(
    db       = 'umbric',
    host     = 'ls-463b324eb918c38c0693a35e6331566693ee1edf.ctgbh4sn1ejq.us-east-1.rds.amazonaws.com',
    port     = 3306,
    user     = 'dbmasteruser',
    password = 'egabrag1!garbage'
)

db_cursor = db_conn.cursor()


@home.route('/', methods=['GET'])
def index():

    states = []
    regions = []
    locations = []
    competitors = []

    try:
        states_sql = "SELECT DISTINCT(location_state) FROM umbric.locations_home"
        db_cursor.execute(states_sql)
        state_rows = db_cursor.fetchall()
        states = [state[0] for state in list(state_rows)]

        distance_sql = "SELECT DISTINCT location_region, location_origin FROM umbric.locations_distances"
        db_cursor.execute(distance_sql)
        distance_rows = db_cursor.fetchall()
        regions = [distance[0] for distance in list(distance_rows) if distance[0] is not None]
        locations = [distance[1] for distance in list(distance_rows) if distance[1] is not None]

        regions = list(dict.fromkeys(regions))
        locations = list(dict.fromkeys(locations))

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
        locations= locations,
        competitors=competitors
    )

@home.route('/search', methods=['POST'])
def search():
    try:
        form_data = request.form.to_dict()
        if not form_data.get('location'):
            raise Exception('Location could not found')

        location_sql = f"SELECT location_destination, location_distance  FROM umbric.locations_distances WHERE location_origin = '{form_data.get('location')}'"
        db_cursor.execute(location_sql)
        location_rows = db_cursor.fetchall()

        coupons = []
        coupon_columns = ['coupon_text', 'coupon_service', 'coupon_lastseen', 'coupon_category', 'coupon_type']
        for location in list(location_rows):
            coupon_sql = f"SELECT DISTINCT coupon_text, coupon_service, coupon_lastseen, coupon_category, coupon_type FROM umbric.locations_coupons WHERE location_destination = '{location[0]}'"
            db_cursor.execute(coupon_sql)
            coupon_rows = db_cursor.fetchall()

            data = [dict(zip(coupon_columns, row)) for row in list(coupon_rows)]

            for d in data:
                try:
                    d['coupon_lastseen'] = d['coupon_lastseen'].isoformat()
                    d['destination'] = location[0]
                    d['distance'] = location[1]
                    d['competitor'] = form_data.get('competitor')
                    d['note'] = f"{d['coupon_text']} {d['coupon_service']} ({'{:.1f}'.format(d['distance'])}m - {d['competitor']} @ {d['destination'].split(',')[0]} - Seen: {d['coupon_lastseen'].split('T')[0]})"
                except:
                    continue

            coupons.extend(data)

        # Close db connection
        # db_conn.close()

        return jsonify({
            "success": True,
            "data": coupons,
        })

    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 400
