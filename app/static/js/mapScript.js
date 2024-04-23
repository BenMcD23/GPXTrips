// get all the routes
var user_routes;
// Get all friend routes
var friend_routes;

$(document).ready(function()
{
  $.ajax({ 
    type: "GET",
    url: "/getUserRoute", 
    dataType: "json",  
    success: function(response_data){
        user_routes = response_data;
    },
    error : function(request,error)
    {
    alert("request failed");
    }
  })

  $.ajax({ 
    type: "GET",
    url: "/getFriendRoute", 
    dataType: "json",  
    success: function(response_data){
        friend_routes = response_data;
    },
    error : function(request,error)
    {
    alert("request failed");
    }
  })

  $('#friendRoutes').hide()


  $('#linkOne').click(function(){
        $('#linkTwo').removeClass('active');
        $('#linkOne').addClass('active');
        $('#friendRoutes').hide()
        $('#myRoutes').fadeIn(450);
  })

  $('#linkTwo').click(function(){
        $('#linkOne').removeClass('active');
        $('#linkTwo').addClass('active');
        $('#myRoutes').hide()
        $('#friendRoutes').fadeIn(450);
  })

  // Enables buttons on pop-up for unsubscribed users
  let button = document.getElementById("subButton")
  let radioButton1 = document.getElementById("radio1")
  let radioButton2 = document.getElementById("radio2")
  let radioButton3 = document.getElementById("radio3")
  if (button) {
    button.style.pointerEvents = 'auto';
  }
  if (radioButton1) {
      radioButton1.style.pointerEvents = 'auto';
  }
  if (radioButton2) {
      radioButton2.style.pointerEvents = 'auto';
  }
  if (radioButton3) {
      radioButton3.style.pointerEvents = 'auto';
  }
  // Also enable the logout button so user can logout if they don't wish to subscribe
  let logoutButton = document.getElementById("logoutLink")
  logoutButton.style.pointerEvents = 'auto';
  let profileButton = document.getElementById("profileLink")
  profileButton.style.pointerEvents = 'auto';
  

})

// listens for when checkbox's are checked
let checkboxes = $("input[type=checkbox][name=addToMap]")

checkboxes.change(function() {
  displayOnMap(this.id, false);
});

// listens for when friend checkboxes are checked
let friendcheckboxes = $("input[type=checkbox][name=friendAddToMap]")
friendcheckboxes.change(function() {
  displayOnMap(this.id, true);
});

// initialize Leaflet

// add the OpenStreetMap tiles

var map = L.map('map').setView([51.505, -0.09], 13);
//Copyright Information
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

// for scale bar, bottom left
L.control.scale({imperial: true, metric: true}).addTo(map);


let GPX = {};
// ran when a checkbox is checked
function displayOnMap(id, isFriendRoute) {
  // get if its been checked or unchecked
  const checkbox_state = document.getElementById(id);

  // if its checked
  if (checkbox_state.checked) {
    // Determines whether the route to be shown is a friend route or not
    // Can then use this to get the correct route to pass to the API
    let route_array = [];
    // Friend routes displayed as green, personal routes are displayed as red
    let chosen_color = 'blue';
    if (isFriendRoute){
      route_array = friend_routes[id]
      fileName = friend_routes[id+"_name"]
      chosen_color = 'green';
    }
    else{
      route_array = user_routes[id]
      fileName = user_routes[id+"_name"]
    }
    

    // create route object
    let newGPX = new L.GPX(route_array, {
      async: true,
      polyline_options: {
        color: chosen_color
      },
      marker_options: {
        startIconUrl: 'static/images/pinstart.png',
        endIconUrl:   'static/images/pinend.png',
        shadowUrl: null,
      },
    }).bindPopup("<h5>File Name:</h5>" + fileName);

    // add to dic
    GPX[id] = newGPX;
    // load it onto map
    newGPX.on('loaded', function(e) {
      var gpx = e.target;
      map.fitBounds(gpx.getBounds());
    }).addTo(map);


  } 
  // if box been unchecked
  else {
    // remove it from the map
    GPX[id].remove(map);
 }
}


//JS Code to handle pop-up forms (Manage GPX Files)
document.addEventListener('DOMContentLoaded', function () {
  const viewRoutesBtn = document.getElementById('viewRoutesBtn');
  const popupContainer = document.getElementById('popupContainer');
  const closeBtn = document.getElementById('closeBtn');

  viewRoutesBtn.addEventListener('click', function () {
      popupContainer.style.display = 'block';
      viewRoutesBtn.style.display = 'none';
  });

  closeBtn.addEventListener('click', function () {
      popupContainer.style.display = 'none';
      viewRoutesBtn.style.display = 'block';
  });
});

//JS Code to handle pop-up forms (Journey Stats)
var viewInfoButtons = document.querySelectorAll('.viewInfoBtn');

// Loop through each button and add click event listener
viewInfoButtons.forEach(function(button) {
    button.addEventListener('click', function() {
        var routeId = button.getAttribute('data-route-id');
        var popupContainer = document.getElementById('popupDataContainer_' + routeId);
        popupContainer.style.display = 'block';
    });
});

// Loop through each friend button and add click event listener
var friendViewInfoButtons = document.querySelectorAll('.friendViewInfoBtn');
friendViewInfoButtons.forEach(function(button) {
  button.addEventListener('click', function() {
      var routeId = button.getAttribute('data-route-id');
      var popupContainer = document.getElementById('friend_popupDataContainer_' + routeId);
      popupContainer.style.display = 'block';

  });
});


// Get all close buttons
var closeButtons = document.querySelectorAll('.closeBtn');

// Loop through each close button and add click event listener
closeButtons.forEach(function(closeBtn) {
    closeBtn.addEventListener('click', function() {
        var routeId = closeBtn.getAttribute('data-route-id');
        var popupContainer = document.getElementById('popupDataContainer_' + routeId);
        popupContainer.style.display = 'none';

    });
});

// Get all close buttons
var friendCloseButtons = document.querySelectorAll('.friendCloseBtn');

// Loop through each friend sclose button and add click event listener
friendCloseButtons.forEach(function(closeBtn) {
    closeBtn.addEventListener('click', function() {
        var routeId = closeBtn.getAttribute('data-route-id');
        var popupContainer = document.getElementById('friend_popupDataContainer_' + routeId);
        popupContainer.style.display = 'none';

    });
});