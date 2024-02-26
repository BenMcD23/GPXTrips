// get all the routes
var user_routes;
function getRoutes(){
  $.ajax({ 
    type: "GET",
    url: "/getRoute", 
    dataType: "json",  
    success: function(response_data){
        user_routes = response_data;
    },
    error : function(request,error)
    {
    alert("request failed");
    }
  });
}

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
function displayOnMap(id) {
  // get if its been checked or unchecked
  const checkbox_state = document.getElementById('displayCheckbox'+id);

  // if its checked
  if (checkbox_state.checked) {
    // create route object
    let newGPX = new L.GPX(user_routes[id], {
      async: true,
      marker_options: {
        startIconUrl: 'static/pinstart.png',
        endIconUrl:   'static/pinend.png',
        shadowUrl: null,
      },
    });

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