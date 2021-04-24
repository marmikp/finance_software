window.onload = function()
{
     $(":text").attr('autocomplete', 'off');  // Here frmAccount indicates id of the form.
}

function showNoti(a,b){
     $.notify({
        icon: "",
        message: b

    }, {
        type: a,
        timer: 1000,
        placement: {
            from: "top",
            align: "center"
        }
    });
    }

$('form').trigger('reset');
$('form').submit(function(e){
    element = $(this);
    $.ajax({
        url:element.attr("url"),
        type:'post',
        data:element.serialize(),
        success:function(response){
            // alert(response);
            showNoti("success",response);
           
        }
    });

     element.trigger("reset");
     $('.pop-up').removeClass('appear');
});

 $('#pop-up-out').click(function(){
        $('.pop-up').removeClass('appear');
    });

       
var scope_holder;
app = angular.module('myApp', []);
app.controller('customersCtrl', function($scope, $http) {
     scope_holder = $scope;
     $scope.get_product_type = function() {
        name = $('#product_name').val();
        var post = $http({
                            method: "GET",
                            url: "utils/get_product_type.php?name="+name,                
                            headers: { "Content-Type": "application/json" }
                        }).then(function(response) {
                        // alert(JSON.stringify(response.data));
                      $scope.product_type_data = response.data;
                      //alert(response.data);
                      var arr = []
                      obj = JSON.parse(JSON.stringify(response.data));
                      for(var x in obj){
                          arr.push(obj[x].product_type);
                      }
                      console.log(arr);
                     try {
                        $( "#text_product_type" ).autocomplete({
                            source: arr
                          }); 
                     } catch (error) {
                         console.log(error);
                     }

                    });
          1
    };
    $scope.get_bills = function(id="",is_bill=""){

        $http({
                            method: "GET",
                            url: "utils/get_bills.php?id="+id+"&is_bill="+is_bill,                
                           headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
                        }).then(function(response) {
                       // alert(JSON.stringify(response.data))
                 $scope.bills_data =  response.data;
                    });
          
                
    };

    

    $scope.get_bills_report = function(){
        bill_type = $('#bill_type').val();
        date1 = $('#date1').val();
        date2 = $('#date2').val();

        bill_type = (typeof bill_type === 'undefined') ? "" : bill_type;
        date1 = (typeof date1 === 'undefined') ? "" : date1;
        date2 = (typeof date2 === 'undefined') ? "" : date2; 
        // alert(bill_no);
           $http({
        method: "post",
        url: "utils/get_bill_report.php",
        data: {
            bill_type:  bill_type,
            date1:  date1,
            date2:  date2
            
        },
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    }).then(function(response) {
         $scope.bills_report = response.data.bills;
         // alert(JSON.stringify(response.data));
         obj = JSON.parse(JSON.stringify(response.data.bills));
         $scope.effective_amount_total= 0;
         $scope.total_amount= 0;

         for(x in obj){
            $scope.effective_amount_total += parseInt(obj[x].effective_amount);
            $scope.total_amount += parseInt(obj[x].amount);
         }

     });

     
    };


    $scope.get_daily_exp = function(){

        date1 = $('#date1').val();
        date2 = $('#date2').val();

        date1 = (typeof date1 === 'undefined') ? "" : date1;
        date2 = (typeof date2 === 'undefined') ? "" : date2; 

          $http({
        method: "post",
        url: "utils/get_daily_exp_report.php",
        data: {
            date1:  date1,
            date2:  date2
            
        },
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    }).then(function(response) {
         $scope.daily_exp_report = response.data.daily_exp;
         // alert(JSON.stringify(response.data));
         $scope.daily_exp_total=0;
        
         obj = JSON.parse(JSON.stringify(response.data.daily_exp));
         

         for(x in obj){
            if(obj[x].add_minus == 0){
                $scope.daily_exp_total += parseInt(obj[x].amount);
            }else{
                 $scope.daily_exp_total -= parseInt(obj[x].amount);
            }
         }
     });


    };


    $scope.get_stock_report = function(){

        product = $('#product').val();
        date1 = $('#date1').val();
        date2 = $('#date2').val();

        product = (typeof product === 'undefined') ? "" : product;
        date1 = (typeof date1 === 'undefined') ? "" : date1;
        date2 = (typeof date2 === 'undefined') ? "" : date2; 

         $http({
        method: "post",
        url: "utils/get_stock_report.php",
        data: {
            product:  product,
            date1:  date1,
            date2:  date2
            
        },
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    }).then(function(response) {
        // alert(JSON.stringify(response.data));
         $scope.stock_report = response.data.stock;
         
         obj = JSON.parse(JSON.stringify(response.data.stock));
         // alert(obj[0].id);
         $scope.total_amount= 0;

         for(x in obj){
            $scope.total_amount += parseInt(obj[x].amount);
         }

     });


    };

    $scope.expand_row = function($event){
        element  = $event.target.parentElement
        // alert($(element).attr(''));
        if(!$(element).hasClass('active')){
            $(element).toggleClass("active", "").nextUntil('.header').css('display', 'table-row');
        }else{
            $(element).toggleClass("active", "").nextUntil('.header').css('display', 'none');
            
        }
    };

    $scope.delete_party = function($event, obj){
        if(confirm("Are you sure you want to delete "+obj.party_name+" ?")){
            $.post('utils/delete_party.php', { id: obj.id, is_bill: obj.is_bill}, 
                function(response){
                     showNoti("success",response);
                     $scope.get_bills_report();
            });
        }
    };


    $scope.delete_daily_exp = function($event, obj){
        if(confirm("Are you sure you want to delete "+obj.date+" of amount "+obj.amount+" ?")){
            $.post('utils/delete_daily_exp_data.php', { id: obj.id}, 
                function(response){
                     showNoti("success",response);
                     $scope.get_daily_exp();
            });
        }
    };


    $scope.delete_product = function($event, obj, all){
        if(confirm("Are you sure you want to delete "+obj.product+" ?")){
            $.post('utils/delete_product.php', { id : obj.id,
                                                product: obj.product, 
                                                product_type: obj.product_type,
                                                all: all}, 
                function(response){
                     showNoti("success",response);
                     $scope.get_stock_report();
            });
        }
    };

 

});
app.filter( 'pay_receive_filter', function() {
    return function( input ) {
        if(input==1){return "Customer";}else{ return "Vendor";}
        }
});

app.filter( 'add_less', function() {
    return function( input ) {
        if(input==1){return "LESS";}else if(input==0){ return "ADD";}
        if(input==11){return "Customer";}else if(input==10){ return "Vendor";}

        }
});

app.filter( 'remove_extra_bills', function() {
    return function( it ) {
        try{
            var input = JSON.parse(JSON.stringify(it));
            var final = []
            for(var i in input){
                if('effective_amount' in  input[i]){
                   if(parseInt(input[i]['effective_amount'] ) !=0){
                     final.push(input[i])
                   }
                }
            }

            return final;
        }catch(err){
            return it;
        }
        }
});

app.filter( 'add_credit_debit', function() {
    return function(it) {
        try{
            var input = JSON.parse(JSON.stringify(it));
            for(var i in input){
                if('amount' in  input[i]){
                    if("pay_receive" in input[i]){
                         am = input[i]['pay_receive'];
                         delete input[i]['pay_receive'];
                         input[i]['add_minus'] = am;
                        }

                
                    amount = input[i]['amount'];
                    delete input[i]['amount']
                    if(input[i]['add_minus'] == "0" || input[i]['add_minus'] == "00"){
                        input[i]['credit'] = amount;
                        input[i]['debit'] = 0;
                    }else{
                        input[i]['Credit'] = 0;
                        input[i]['Debit'] = amount;
                    }
                }
            }

            return input;
        }catch(err){
            return it;
        }
        }
});