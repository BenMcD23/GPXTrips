// initialize Leaflet
var map = L.map('map').setView({lon: 0, lat: 0}, 2);

// add the OpenStreetMap tiles
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
maxZoom: 19,
attribution: '&copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap contributors</a>'
}).addTo(map);

// for scale bar, bottom left
L.control.scale({imperial: true, metric: true}).addTo(map);

// shows gpx track on map, currently just one static file
new L.GPX('static/bennevis.gpx', {
    async: true,
    marker_options: {
      startIconUrl: 'static/pinstart.png',
      endIconUrl:   'static/pinend.png',
      shadowUrl: null,
    },
  }).on('loaded', function(e) {
    var gpx = e.target;
    map.fitBounds(gpx.getBounds());
    control.addOverlay(gpx, gpx.get_name());
}).addTo(map);
