from datetime import datetime, timedelta
from .models import Plan, Subscription, SubscriptionStats, Friendship, User
from xml.etree import ElementTree as ET
from geopy.distance import geodesic
from dateutil import parser
from app import db
import gpxpy


# misc func
def getCurrentBuisnessWeek():
    """gets the current buisness week
    starts from the 01/02/2024

    Returns:
        int: number of weeks since the start of the buisness
    """
    # this is the starting week of the buisness, weeks are then itterated from this date
    # there is 0 revenue from before this date
    firstWeek = datetime(2024, 2, 1)
    # this is the diff between the start week and current week
    # so number of weeks since first week
    return (((datetime.now() - firstWeek)).days) // 7


# misc func
def getPrices():
    """just gets the current prices set in db

    Returns:
        array: array of ints of prices
    """
    # get all prices and turn them into an array
    allPlans = Plan.query.all()
    return [i.price_as_pound() for i in allPlans]


# sub func
def current_user_active_subscription(current_user_id):
    """checks if the current user has a sub with auto renewals ON

    Args:
        current_user_id (int): the id of current logged in user

    Returns:
        Bool: true or false
    """
    # query db for the users most recent sub, by date
    latest_subscription = Subscription.query.filter_by(
        user_id=current_user_id).order_by(Subscription.date_start.desc()).first()
    # if it exists
    if latest_subscription:
        return latest_subscription.active
    # otherwise
    return False


# sub func
def current_user_current_subscription(current_user_id):
    """checks if the current user has a sub in general
    not necessarily with auto renewals on

    Args:
        current_user_id (int): the id of current logged in user

    Returns:
        Bool: true or false
    """
    # Current subscription - the user has a current subscription which expires some time in the future, irrespective of cancellation status
    subscriptions = Subscription.query.filter_by(user_id=current_user_id).all()
    for subscription in subscriptions:
        if subscription.date_end > datetime.now():
            return True

    return False


# sub func
def create_subscription(user, plan, subscription_id, customer_id):
    """creates sub in database

    Args:
        user (db obj): the current logged in user as db object
        plan (db obj): the plan the user purchased as db object
        subscription_id (str): the sub id off of stripe
        customer_id (str): the customer id off of stripe
    """
    # calculates how long the sub should last, based on sub purchased
    if plan.name == "Weekly":
        date_end = datetime.now() + timedelta(weeks=1)
    elif plan.name == "Monthly":
        date_end = datetime.now() + timedelta(weeks=4)
    else:
        date_end = datetime.now() + timedelta(weeks=52)

    # creates user sub in database
    subscription = Subscription(
        user=user,
        plan_id=plan.id,
        date_start=datetime.utcnow(),
        date_end=date_end,
        subscription_id=subscription_id,
        customer_id=customer_id,
        active=True
    )

    db.session.add(subscription)
    db.session.commit()

    print(f"Subscription created for {user.email} with plan {plan.name}")


# sub func / stats
def addToStats(subCost):
    """adds each purchase to the stats table
    for each purchase

    Args:
        subCost (int): cost of the sub purchased
    """
    # this is the diff between the start week and current week
    # so number of weeks since first week
    currentWeek = getCurrentBuisnessWeek()

    currentWeekdb = SubscriptionStats.query.filter_by(
        week_of_business=currentWeek).first()

    # if the week of the year already exists in the database, then just add on the revenue
    if currentWeekdb:
        currentWeekdb.total_revenue = currentWeekdb.total_revenue + subCost
        currentWeekdb.num_customers = currentWeekdb.num_customers + 1

    # otherwise create the week in db
    else:
        newWeek = SubscriptionStats(
            week_of_business=currentWeek, total_revenue=subCost, num_customers=1)
        db.session.add(newWeek)

    db.session.commit()


# route func
def getRouteInfoList(inputList, outputList):
    """gets the route info so can display route stats

    Args:
        inputList (array): all the users routes
        outputList (array): the routes stats in a 2d array
    """
    for route in inputList:
        gpx_data_decoded = route.gpx_data.decode('ascii')
        gpx_data = gpx_data_decoded.replace('\\r', '\r').replace('\\n', '\n')
        gpx_data = "".join(gpx_data)[2:][:-1]  # Trim excess characters
        # Calculate route information
        length, duration, start_point, end_point = calculate_route_info(
            gpx_data)
        route_info = {
            'id': route.id,
            'name': route.name,
            'user': {
                'first_name': route.user.first_name,
                'last_name': route.user.last_name
            },
            'length': length,
            'duration': duration,
            'start': start_point,
            'end': end_point,
            'upload_time': route.upload_time.strftime("%Y-%m-%d %H:%M:%S")
        }
        outputList.append(route_info)


# route func
def calculate_route_info(gpx_data, unit='km'):
    """calcualtes all the routes stats

    Args:
        gpx_data (gpx file): the gpx data from the saved gpx file in db
        unit (str, optional): the unit used in stats. Defaults to 'km'.

    Returns:
        stats: the stats displayed on website
    """
    # Parse GPX data
    tree = ET.fromstring(gpx_data)

    # Extract track points
    track_points = [(float(trkpt.attrib['lat']), float(trkpt.attrib['lon']))
                    for trkpt in tree.findall('.//{http://www.topografix.com/GPX/1/1}trkpt')]

    # Calculate route length
    length = sum(geodesic(track_points[i], track_points[i + 1]).meters
                 for i in range(len(track_points) - 1))

    # Convert length to kilometers or miles based on unit preference
    if unit == 'km':
        length = length / 1000  # Convert meters to kilometers
        length = round(length, 2)  # Round to 2 decimal places
        length = f"{length} km"  # Append unit
    elif unit == 'miles':
        length = length * 0.000621371  # Convert meters to miles
        length = round(length, 2)  # Round to 2 decimal places
        length = f"{length} miles"  # Append unit
    else:
        # Default to meters if unit is not km or miles
        length = f"{length} meters"

    times = tree.findall(".//time")
    timestamps = [parser.isoparse(time.text) for time in times]

    # Calculate route duration if timestamps are available
    duration = 0
    if timestamps:
        duration = (max(timestamps) - min(timestamps)).total_seconds()

    # Start and end points
    start_point = (0, 0)
    end_point = (0, 0)
    if track_points:
        start_point = round(track_points[0][0], 3), round(
            track_points[0][1], 3)
        end_point = round(track_points[-1][0],
                          3), round(track_points[-1][1], 3)

    return length, duration, start_point, end_point


# route func/checks gpx
def is_valid_gpx_structure(gpx_data):
    """checks if the gpx file is a valid gpx file

    Args:
        gpx_data (gpx file): the gpx data uploaded

    Returns:
        Bool: if its a valid gpx or not
    """
    try:
        # Parse GPX data
        gpx = gpxpy.parse(gpx_data)
        # No exception means the GPX data is structurally valid
        return True, None
    except gpxpy.gpx.GPXException as e:
        error_message = f"GPX parsing error: {e}"
        return False, error_message


# friend func
def friendUser(user_friend_id, current_user_id):
    """creates the relationship between 2 users

    Args:
        user_friend_id (int): user going to friend id
        current_user_id (int): current logged in user id
    """
    # create the friendship relationship
    friendship = Friendship(
        user1_id=current_user_id,
        user2_id=user_friend_id
    )

    db.session.add(friendship)
    db.session.commit()


# friend func
def getFriends(current_user_id):
    """gets all the outgoing and incoming friends 

    Args:
        current_user_id (int): current logged in user id

    Returns:
        array: array of friends
    """
    # get all the outgoing and incoming friends
    outgoingfriendships = Friendship.query.filter_by(
        user1_id=current_user_id).all()
    incomingfriendships = Friendship.query.filter_by(
        user2_id=current_user_id).all()

    friends = []

    # for all the friendships, add to array
    for friendship in outgoingfriendships:
        friends.append(User.query.get(friendship.user2_id))

    for friendship in incomingfriendships:
        friends.append(User.query.get(friendship.user1_id))

    return friends
