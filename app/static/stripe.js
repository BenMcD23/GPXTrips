fetch("/stripe")
    .then((result) => {
        return result.json();
    })
    .then((data) => {
        const stripe = Stripe(data.publicKey);

        // Function to handle subscription button clicks
        const handleSubscriptionClick = (planDuration) => {
            fetch(`/checkout?plan_duration=${planDuration}`)
                .then((result) => result.json())
                .then((data) => {
                    console.log(data);
                    return stripe.redirectToCheckout({
                        sessionId: data.sessionId,
                    });
                })
                .then((res) => {
                    console.log(res);
                });
        };


        $("#subButton").click(function(){
            var subPlan = $("input[name='pp']:checked").val();
            if(subPlan == "Year")
            { // Year Subsciption
                handleSubscriptionClick("1_year");
            }
            else if(subPlan == "Month")
            { // Month Subscription
                handleSubscriptionClick("1_month");
            }
            else
            { // Week Subscription
                handleSubscriptionClick("1_week");
            }
        });

    });
