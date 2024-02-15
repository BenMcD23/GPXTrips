
// initialize Leaflet
var map = L.map('map').setView({lon: 0, lat: 0}, 2);

// add the OpenStreetMap tiles
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
maxZoom: 19,
attribution: '&copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap contributors</a>'
}).addTo(map);

// for scale bar, bottom left
L.control.scale({imperial: true, metric: true}).addTo(map);

// converts passed GPX into something the API can use
// why? as when passing the route, all the <> turned into &lt and &gt
var gpxConvert = function(convert){
  return $("<span />", { html: convert }).text();
};