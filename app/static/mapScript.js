
// initialize Leaflet

// add the OpenStreetMap tiles
var map = L.map('map').setView([51.505, -0.09], 13);
//Copyright Information
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

// for scale bar, bottom left
L.control.scale({imperial: true, metric: true}).addTo(map);

// converts passed GPX into something the API can use
// why? as when passing the route, all the <> turned into &lt and &gt
var gpxConvert = function(convert){
  return $("<span />", { html: convert }).text();
};