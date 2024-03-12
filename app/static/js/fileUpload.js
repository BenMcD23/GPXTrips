document.getElementById('fileUploadForm').addEventListener('submit', function (e) {
    e.preventDefault();

    var fileInput = document.getElementById('fileInput');
    var file = fileInput.files[0];

    if (file) {
        var formData = new FormData();
        formData.append('file', file);

        // Retrieve the CSRF token from the form and include it in the FormData
        var csrfToken = document.querySelector('input[name="_csrf_token"]').value;
        formData.append('_csrf_token', csrfToken);

        console.log('Sending file to server...');
        
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (response.headers.get('content-type') && response.headers.get('content-type').includes('application/json')) {
                return response.json();
            } else {
                return response.text(); // or response.blob(), depending on the actual response format
            }
        })
        .then(data => {
            console.log('Server response:', data);
        
            if (typeof data === 'object' && data.error) {
                console.error('Error uploading file:', data.error);
            } else if (typeof data === 'string') {
                console.log('Non-JSON response:', data);
                // Handle non-JSON response (if needed)
            } else {
                document.getElementById('result').innerHTML = data.message;

                // Fetch updated routes and update the table in user.html
                updateRoutesTable();
            }
        })
        .catch(error => {
            console.error('Error uploading file:', error.message);
            document.getElementById('result').innerHTML = 'Error uploading file: ' + error.message;
        });
    } else {
        console.log('No file selected');
        document.getElementById('result').innerHTML = 'Please select a file';
    }
});

// Function to update the table in user.html
function updateRoutesTable() {
    // Fetch the updated routes
    $.ajax({
        type: "GET",
        url: "/getRouteForTable",
        dataType: "json",
        success: function(routeInfoList) {
            // Update the table with the new routes data
            var tableBody = $('#table');
            tableBody.empty(); // Clear existing rows

            routeInfoList.forEach(function(routeInfo, index) {
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
                '</tr>';
            
                tableBody.append(newRow);
            });
        },
        error: function(request, error) {
            console.error("Error fetching routes:", error);
        }
    });
}

// Event delegation for 'View Info' button
$(document).on('click', '.viewInfoBtn', function() {
    var routeId = $(this).data('route-id');
    // Your code to handle the 'View Info' button click, e.g., show the popup for the corresponding routeId
    var popupContainer = $('#popupDataContainer_' + routeId);
    popupContainer.show();
});

$(document).on('click', '.closeBtn', function() {
    var routeId = $(this).data('route-id');
    // Your code to handle the close button click, e.g., hide the corresponding popup
    var popupContainer = $('#popupDataContainer_' + routeId);
    popupContainer.hide();
});
