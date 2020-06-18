function updateTable() {  
  console.log("Updating table...")
    $.ajax({
      url: "/stock_data",
      type: "get",
      success: function(response) {
        $("#stocks_table").html(response);
        console.log("Table updated!");
        cellColor();
        document.querySelector("#loader").style.display = "none"; 
        document.querySelector("body").style.visibility = "visible"; 
      },
      error: function(xhr) {
        console.log("Error updating table. Trying again after 2 minutes...")
      }
    });
}
function cellColor(){
  console.log("Setting cell colors...")
  var cells = document.getElementsByClassName("stock-data");
  for (var i = 0; i < cells.length; i++) {
      if (parseInt(cells[i].getElementsByClassName('stock_percentage')[0].innerHTML) >= 0) {
          cells[i].style.backgroundColor = "#90ee90";
      }
      else{
        cells[i].style.backgroundColor = "#ff7f7f";
      }
  }
  console.log("Cell colors set!")
}
function load(){
  console.log("Loading page...")
  setInterval(updateTable, 120 * 1000);
}