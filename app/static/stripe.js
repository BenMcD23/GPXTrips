fetch("/stripe")
.then((result) => {return result.json();} )
.then((data) => {
    const stripe = Stripe(data.publicKey)

    // Handle 1 year subscription button
    document.querySelector("#oneYearSubButton").addEventListener("click", () => {
    // Get Checkout Session ID
    fetch("/checkout")
    .then((result) => { return result.json(); })
    .then((data) => {
      return stripe.redirectToCheckout({sessionId: data.sessionId})
    })
    .then((res) => {
      console.log(res);
    });
  });
});