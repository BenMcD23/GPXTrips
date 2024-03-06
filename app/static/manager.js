// on load
$(document).ready(function()
{
    // gets the csrfToken, this is so can use ajax post
    var csrf_token = $('#csrfToken').data('value');
    // need to setup ajax with csrfToken, otherwise wont work
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrf_token);
            }
        }
    });
})

// gets all the checkbox's
let checkboxes = $("input[type=checkbox][name=userState]")

// listens for when any of them get checked/unchecked
checkboxes.change(function() {
    changeUserState(this.id);
});

function changeUserState(id){
    const checkbox_state = document.getElementById(id);
    var state;
    // if gets checked
    if (checkbox_state.checked) {
        $("#text_"+id).text("True");
        state = true;
    }

    // if it gets unchecked
    else {
        $("#text_"+id).text("False");
        state = false
    }

    // then post the state with the id, so can be changed in database
    $.ajax({ 
        url: '/accountState', 
        type: 'POST', 
        contentType: 'application/json', 
        data: JSON.stringify({id, state}), 
    
    // if success, dont do anything
    success: function(response) {
        
    },
    // if error, console error
    error: function(error) { 
        console.log(error); 
    } 
    });
}

// email search
$(document).ready(function(){
    var emails=[];
    
    function getEmails(){
        // get all the emails from database
        $.getJSON('/emails', function(data, status, xhr){
            // add them all to the array
            for (var i = 0; i < data.length; i++ ) {
                emails.push(data[i].email);
            }
    });
    };
    
    // call get emails
    getEmails();

    // autocomplete the search box
    $('#userEmail').autocomplete({
        source: emails,
        });
    });
