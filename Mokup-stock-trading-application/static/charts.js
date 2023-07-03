document.addEventListener('DOMContentLoaded', function(){

    const ctx = document.getElementById('myChart');
    //Get all the needed elements from the table
    
    let  table_labels = document.getElementsByClassName('stock_symbol');
    let table_data = document.getElementsByClassName('total_value');
    
    const chart_labels = [];
    const chart_data = [];
    
    //Populate a list for the labels and a list for the data.
    for (let i = 0; i < table_labels.length; i++) {
        chart_labels[i] = table_labels[i].innerHTML;
      }
    
    for (let i = 0; i < table_data.length; i++) {
        chart_data[i] = parseFloat(table_data[i].innerHTML.replaceAll('$','').replaceAll(',','')); //Convert the string into floats
    }
    
    let cash = parseFloat(document.getElementById('wallet_cash').innerHTML.replaceAll('$','').replaceAll(',',''))
    let total = parseFloat(document.getElementById('wallet_total').innerHTML.replaceAll('$','').replaceAll(',',''))
    
    // Add the cash value to the label and data lists.
    chart_labels.push('cash');
    chart_data.push(cash);
    
    console.log(chart_labels);
    console.log(chart_data);
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
          labels: chart_labels,
          datasets: [{
            label: 'shares',
            data: chart_data,
            borderWidth: 1
          }]
    
        },
        options: {
            borderWidth: 5,
            borderRadius: 2,
            responsive: true
        }
      });
    
    });
    