// Call the dataTables jQuery plugin
$(document).ready(function() {
  $('#dataTable').DataTable();
});

// Call the dataTables jQuery plugin
$(document).ready(function() {
  $('#sampleTable').DataTable();
});

// Call the dataTables jQuery plugin
$(document).ready(function() {
  $('#yahootable').DataTable();
});

// Call the dataTables jQuery plugin
$(document).ready(function() {
  $('#predictions').DataTable();  
});


var oTable = $('#predtictontable').DataTable({ 
  'rowCallback': function(row, data, index){
  if(data[4] == 'Strong Buy'){
      $(row).find('td:eq(4)').css('color', 'green');
  }
  if(data[4] == 'Strong Sell'){
    $(row).find('td:eq(4)').css('color', 'red');
  }
},
"ordering": false

});

var oTable = $('#wstbuy').DataTable({ 
  'rowCallback': function(row, data, index){
  if(data[4] == 'Strong Buy'){
      $(row).find('td:eq(4)').css('color', 'green');
  }
  if(data[4] == 'Strong Sell'){
    $(row).find('td:eq(4)').css('color', 'red');
  }
},
"ordering": false

});




var oTable = $('#yahoostbuy').DataTable({ 
  'rowCallback': function(row, data, index){
  if(data[4] == 'Strong Buy'){
      $(row).find('td:eq(4)').css('color', 'green');
  }
  if(data[4] == 'Strong Sell'){
    $(row).find('td:eq(4)').css('color', 'red');
  }
},
"ordering": false

});