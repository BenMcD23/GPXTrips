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

        console.log('Sending file to server...');

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
                updateRoutesTable();
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
        });
    } else {
        // Display error message if no file is selected
        console.log('No file selected');
        document.getElementById('result').innerHTML = 'Please select a file';
    }
});

// Function to update the route table in user.html
function updateRoutesTable() {
    // Fetch updated routes from the server
    $.ajax({
        type: "GET",
        url: "/getRouteForTable",
        dataType: "json",
        success: function(routeInfoList) {
            // Update the table with the new routes data
            var tableBody = $('#table');
            tableBody.empty(); // Clear existing rows

            routeInfoList.forEach(function(routeInfo, index) {
                // Generate HTML for each route row
                var newRow = '<tr>' +
                    '<td>' + routeInfo.name + '</td>' +
                    '<td>' +
                        '<div class="form-check">' +
                            '<input class="form-check-input" type="checkbox" name="addToMap" id="' + routeInfo.id + '">' +
                            '<label class="form-check-label" for="' + routeInfo.id + '"></label>' +
                        '</div>' +
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
                                    '<button>Delete</button>' +
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
        },
        error: function(request, error) {
            // Handle errors during route fetching process
            console.error("Error fetching routes:", error);
        }
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