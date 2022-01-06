function filterFocus(elm) {
    // Change colors of buttons to match current filter
    $('div.filter-button').removeClass('cg-blue').addClass('w3-light-grey')
    $(elm).addClass("selected").addClass('cg-blue').removeClass('w3-light-grey')

    // Add id_filter query param to search target
    const idFilter = $(elm).attr("id-filter")
    $("[name='id_filter']").attr("value", idFilter)
}
