function updateTable() {  
  console.log("Updating table...");
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
        console.log("Error updating table. Trying again after 2 minutes...");
      }
    });
}
function cellColor(){
  console.log("Setting cell colors...");
  var cells = document.getElementsByClassName("stock-data");
  for (var i = 0; i < cells.length; i++) {
      if (parseFloat(cells[i].getElementsByClassName('stock_percentage')[0].innerHTML.replace('%','')) >= 0) {
          cells[i].style.backgroundColor = "#90ee90";
      }
      else{
        cells[i].style.backgroundColor = "#ff7f7f";
      }
  }
  console.log("Cell colors set!");
}
function updateNews() {  
  console.log("Getting news...");
    $.ajax({
      url: "/stock_news",
      type: "get",
      success: function(response) {
        $("#news").html(response);
        console.log("News updated!");
      },
      error: function(xhr) {
        console.log("Error updating news. Trying again after 2 minutes...");
      }
    });
}
function load(){
  console.log("Loading page...");
  updateTable();
  updateNews();
  setInterval(updateTable, 60 * 1000);
  setInterval(updateNews, 600 * 1000);
}