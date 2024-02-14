from app import db, models

def create_route_test():
    # Generate BLOB from GPX data file
    with open('app/static/bennevis.gpx', 'r') as f:
        data = f.read()

    gpx_blob = data.encode('ascii')

    route = models.Route(
        gpx_data=gpx_blob
    )
    db.session.add(route)
    db.session.commit()

def get_route_test():
    route = models.Route.query.get(1)

    gpx = route.gpx_data.decode('ascii')

    print(gpx)
