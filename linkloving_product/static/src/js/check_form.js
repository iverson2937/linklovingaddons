/**
 * Created by 123 on 2017/7/6.
 */

$(".MySteps").parent().next(".modal-footer").hide()
var flag = 1;
$(".pre_step").click(function () {
    if(flag==1){

    }else {
        $(".next_step").show();
        $(".mysteps_save").hide();
        console.log(flag)
        $(".step"+flag).hide();
        $(".step_nav"+flag).removeClass("active_step");
        flag--;
        $(".step"+flag).show();
         $(".next_step").html("下一步");
    }
});
$(".next_step").click(function () {
    if(flag==5){

    }else {
        if(flag==3){
            $(".next_step").hide();
            $(".mysteps_save").css("display","inline-block")
        }
        if(flag==4){
            $(".MySteps footer").hide();
        }
        $(".step"+flag).hide();
        flag++;
        $(".step"+flag).show();
        $(".step_nav"+flag).addClass("active_step");
    }
});

$(".mysteps_save").click(function () {
    $(document).ajaxComplete(function (event, xhr, settings) {
        // console.log(settings)
        console.log(event);
        console.log(xhr);
        var data = JSON.parse(settings.data);
        var result = JSON.parse(xhr.responseText);
        console.log(result);
        if (data.params.method == 'create' && !result.error) {
            console.log(data);
            // $(".MySteps .step4").hide();
            console.log(flag);
            $(".step"+flag).hide();
            $(".MySteps .step5").show();
            console.log(flag);
            $(".MySteps footer").hide();
        }
    })
})