
function getCountdown(nextGame, includeUnits=false) {
  // Set the date we're counting down to
  var countDownDate = new Date(nextGame).getTime();

  // Update the count down every 1 second
  var x = setInterval(function() {

    // Get today's date and time
    var now = new Date().getTime();

    // Find the distance between now and the count down date
    var distance = countDownDate - now;

    // Time calculations for days, hours, minutes and seconds
    var days = Math.floor(distance / (1000 * 60 * 60 * 24));
    var hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
    var seconds = Math.floor((distance % (1000 * 60)) / 1000);

    var daysUnit = ""
    var hoursUnit = ""
    var minsUnit = ""
    var secsUnit = ""

    if (includeUnits === true) {
      daysUnit = days === 1 ? " day" : " days"
      hoursUnit = hours === 1 ? " hour" : " hours"
      minsUnit = minutes === 1 ? " minute" : " minutes"
      secsUnit = seconds === 1 ? " second" : " seconds"
    }

    // Display the result in the element
    document.getElementById("days").innerHTML = days.toString() + daysUnit;
    document.getElementById("hours").innerHTML = hours.toString() + hoursUnit;
    document.getElementById("mins").innerHTML = minutes.toString() + minsUnit;
    document.getElementById("secs").innerHTML = seconds.toString() + secsUnit;

    // If the count down is finished, write some text
    if (distance < 0) {
      clearInterval(x);
      document.getElementById("demo").innerHTML = "EXPIRED";
    }
  }, 1000);

}
