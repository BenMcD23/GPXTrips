// listens for change in downdown menu, then changes div
$(document).ready(function(){
    $("select").change(function(){
        $(this).find("option:selected").each(function(){
            var optionValue = $(this).attr("value");
            if(optionValue){
                $(".chart").not("." + optionValue).hide();
                $("." + optionValue).show();
            } else{
                $(".chart").hide();
            }
        });
    }).change();
});