/**
 * Created by 123 on 2017/7/6.
 */

$(".MySteps").parent().next(".modal-footer").hide()
var flag = 1;
$(".pre_step").click(function () {
    if(flag==1){

    }else {
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
            $(".next_step").html("保存");
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