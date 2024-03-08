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
                document.getElementById('result').innerHTML = 'File uploaded successfully: ' + data.message;

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
            // Assuming you have a table with ID 'routesTable' in user.html
            $('#table').empty(); // Clear existing rows

            routeInfoList.forEach(function(routeInfo, index) {
                var newRow = '<tr>' +
                    '<td>' + routeInfo.name + '</td>' +
                    '<td>' + routeInfo.upload_time + '</td>' +
                    '<td>' +
                        '<div class="form-check">' +
                            '<input class="form-check-input" type="checkbox" value="" id="displayCheckbox' + routeInfo.id + '" onchange="displayOnMap(' + routeInfo.id + ')">' +
                            '<label class="form-check-label" for="displayCheckbox' + routeInfo.id + '">Show on Map?</label>' +
                        '</div>' +
                    '</td>' +
                    '<td>' +
                        '<div class="form-check">' +
                            '<input class="form-check-input" type="checkbox" value="" id="publicCheckbox' + routeInfo.id + '">' +
                            '<label class="form-check-label" for="publicCheckbox' + routeInfo.id + '">Public</label>' +
                        '</div>' +
                    '</td>' +
                '</tr>';
            
                $('#table').append(newRow);
            });
        },
        error: function(request, error) {
            console.error("Error fetching routes:", error);
        }
    });
}
