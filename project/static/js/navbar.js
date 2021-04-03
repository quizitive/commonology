// --- use this function to register listeners --- //
$(function() {
  // click anywhere closes dropdown
    $(document).bind("click", (event) => {
    showHideDropdown(event)
  })
  // clicking on caret can open or close dropdown
  $("#navbar-dropdown-icon").bind("click", (event) => {
    showHideDropdown(event,true)
  });
})

// --- define listener functionality ---- //
function showHideDropdown(e, canOpen=false) {
  const drpdn = $("#navbar-dropdown-content")
  if (!drpdn.hasClass("w3-show") && canOpen === true) {
    drpdn.addClass("w3-show")
    e.stopPropagation();
  } else {
    drpdn.removeClass("w3-show")
  }
}