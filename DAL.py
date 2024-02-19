from app import db, models

def add_route(data):
    # Generate BLOB from GPX data
    gpx_blob = data.encode('ascii')
    # create database entry, currently RouteTest just for testing
    route = models.Route(
        user_id=0,
        gpx_data=gpx_blob
    )
    # add to database
    db.session.add(route)
    db.session.commit()

def get_route():
    # this needs to be related to user eventually
    route = models.Route.query.get(1)

    # decodes
    gpx = route.gpx_data.decode('ascii')

    return gpx
