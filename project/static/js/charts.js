$(() => {
  $('.chart').each((i, elm) => {
    console.log(elm.id)
    var ctx = elm.getContext('2d');
    var data = JSON.parse(JSON.parse(document.getElementById(elm.id + '-data').textContent));
    var myChart = new Chart(ctx, data);
  })
})

