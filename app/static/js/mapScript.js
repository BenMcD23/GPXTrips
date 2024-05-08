// get all the routes
var user_routes;
// Get all friend routes
var friend_routes;

function getRoutes() 
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
  });

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
  });
  }


$(document).ready(function()
{
  getRoutes();
  $('#friendRoutes').hide()
  console.log("yes");


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
  let homeButton = document.getElementById("homeLink")
  homeButton.style.pointerEvents = 'auto';

})

// listens for when checkbox's are checked
let checkboxes = $("input[type=checkbox][name=addToMap]")

checkboxes.change(function() {
  displayOnMap(this.id, false);
  console.log("yes");
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





// file upload stuff

// Event listener for form submission
document.getElementById('fileUploadForm').addEventListener('submit', function (e) {
  e.preventDefault(); // Prevent default form submission behavior
  
  // Retrieve the selected file from the form input
  var fileInput = document.getElementById('fileInput');
  var file = fileInput.files[0];

  if (file) {
      // Create FormData object to send file data
      var formData = new FormData();
      formData.append('file', file);

      // Retrieve the CSRF token and append it to the FormData
      var csrfToken = document.querySelector('input[name="_csrf_token"]').value;
      formData.append('_csrf_token', csrfToken);

      // Send file data to the server via fetch API
      fetch('/upload', {
          method: 'POST',
          body: formData
      })
      .then(response => {
          // Handle server response
          if (response.headers.get('content-type') && response.headers.get('content-type').includes('application/json')) {
              return response.json();
          } else {
              return response.text(); // or response.blob(), depending on the actual response format
          }
      })
      .then(data => {
          // Process server response data
          console.log('Server response:', data);
      
          if (typeof data === 'object' && data.error) {
              // Display error message if upload fails
              console.error('Error uploading file:', data.error);
              document.getElementById('result').innerHTML = 'Error uploading file: ' + data.error;
          } else if (typeof data === 'object' && data.message) {
              // Display success message if upload succeeds and update route table
              document.getElementById('result').innerHTML = data.message;
              updateRoutesTable(); // Update the routes table after successful upload       
              getRoutes(); // Update the routes, so can put on map
          } else if (typeof data === 'string') {
              // Handle non-JSON response (if needed)
              console.log('Non-JSON response:', data);
              document.getElementById('result').innerHTML = 'Non-JSON response: ' + data;
          }
      })
      .catch(error => {
          // Handle errors during file upload process
          console.error('Error uploading file:', error.message);
          document.getElementById('result').innerHTML = 'Error uploading file: ' + error.message;
      })
      .finally(() => {
          // Reload routes after uploading
          reloadRoutes();
      });
  } else {
      // Display error message if no file is selected
      console.log('No file selected');
      document.getElementById('result').innerHTML = 'Please select a file';
  }
});

// Function to reload routes after uploading
function reloadRoutes() {
  $.ajax({ 
      type: "GET",
      url: "/getRoute", 
      dataType: "json",  
      success: function(response_data){
          user_routes = response_data;
      },
      error : function(request,error) {
          console.error("Error fetching routes:", error);
      }
  });
}

// Function to update the route table in user.html
function updateRoutesTable() {
  $.ajax({
      type: "GET",
      url: "/getRouteForTable",
      dataType: "json",
      success: function(routeInfoList) {
          updateRoutesTableWithState(routeInfoList);
      },
      error: function(request, error) {
          console.error("Error fetching routes:", error);
      }
  });
}

// Define a function to update the routes table without losing checkbox state
function updateRoutesTableWithState(routes) {
  var tableBody = $('#table');
  var checkboxes = {};

  // Store checkbox state before updating the table
  $('input[type=checkbox][name=addToMap]').each(function() {
      checkboxes[this.id] = this.checked;
  });

  tableBody.empty(); // Clear existing rows

  routes.forEach(function(routeInfo) {
      // Generate HTML for each route row
      var newRow = '<tr>' +
          '<td>' + routeInfo.name + '</td>' +
          '<td>' +
              '<label class="switch" for="' + routeInfo.id + '"' + '>' +
                  '<input type="checkbox" name="addToMap" id="' + routeInfo.id + '"' + (checkboxes[routeInfo.id] ? ' checked' : '') + '>' +
                  '<span class="slider"></label>' +
              '</label>' +
          '</td>' +
          '<td>' + routeInfo.user.first_name + ' ' + routeInfo.user.last_name + '</td>' +
          '<td>' +
              '<button class="btn-primary viewInfoBtn" data-route-id="' + routeInfo.id + '">View Info</button>' +
              '<div>' +
                  '<div class="popupDataContainer" id="popupDataContainer_' + routeInfo.id + '">' +
                      '<div class="infoForm">' +
                          '<span class="closeBtn" data-route-id="' + routeInfo.id + '">&times;</span>' +
                          '<h1>Route Information</h1>' +
                          '<p>Route Name: ' + routeInfo.name + '</p>' +
                          '<p>Route Length: ' + routeInfo.length + '</p>' +
                          '<p>Route Duration: ' + routeInfo.duration + '</p>' +
                          '<p>Route Start: ' + routeInfo.start + '</p>' +
                          '<p>Route End: ' + routeInfo.end + '</p>' +
                          '<p>Upload Date: ' + routeInfo.upload_time + '</p>' +
                          '<button class="btn-primary deleteBtn" data-route-id="' + routeInfo.id + '">Delete</button>' +
                      '</div>' +
                  '</div>' +
              '</div>' +
          '</td>' +
          '<td>' +
              '<button class="btn-primary downloadBtn" data-route-id="' + routeInfo.id + '">Download</button>' +
          '</td>' +
      '</tr>';
  
      // Append the new row to the table
      tableBody.append(newRow);
  });

  // Reattach event listeners for checkboxes
  $('input[type=checkbox][name=addToMap]').change(function() {
      displayOnMap(this.id);
  });
}

// Event delegation for 'View Info' button
$(document).on('click', '.viewInfoBtn', function() {
  var routeId = $(this).data('route-id');
  // Handle click event for 'View Info' button
  var popupContainer = $('#popupDataContainer_' + routeId);
  popupContainer.show();
});

// Event delegation for 'Close' button in popup
$(document).on('click', '.closeBtn', function() {
  var routeId = $(this).data('route-id');
  // Handle click event for 'Close' button in popup
  var popupContainer = $('#popupDataContainer_' + routeId);
  popupContainer.hide();
});

// Event delegation for 'Download' button
$(document).off('click', '.downloadBtn').on('click', '.downloadBtn', function(event) {
  event.stopPropagation(); // Stop event propagation to prevent multiple click events
  var routeId = $(this).data('route-id');
  // Trigger file download for the corresponding routeId
  window.location.href = '/download/' + routeId;
});

// Event delegation for 'Delete' button
$(document).off('click', '.deleteBtn').on('click', '.deleteBtn', function(event) {
  event.stopPropagation(); // Stop event propagation to prevent multiple click events
  var routeId = $(this).data('route-id');
  
  // Confirm deletion
  if (confirm('Are you sure you want to delete this route?')) {
      // Send AJAX request to delete route
      window.location.href = '/deleteRoute/' + routeId;
  }
});