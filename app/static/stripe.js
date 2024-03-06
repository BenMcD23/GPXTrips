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

        // Handle 1 year subscription button
        document
            .querySelector("#oneYearSubButton")
            .addEventListener("click", () => {
                handleSubscriptionClick("1_year");
            });

        // Handle 1 month subscription button
        document
            .querySelector("#oneMonthSubButton")
            .addEventListener("click", () => {
                handleSubscriptionClick("1_month");
            });

        // Handle 1 week subscription button
        document
            .querySelector("#oneWeekSubButton")
            .addEventListener("click", () => {
                handleSubscriptionClick("1_week");
            });
    });
