/**
 * Created by 123 on 2017/7/6.
 */

var flag = 1;
$(".pre_step").click(function () {
    if(flag==1){

    }else {
        $(".step"+flag).hide();
        $(".step_nav"+flag).removeClass("active_step");
        flag--;
        $(".step"+flag).show();
    }
});
$(".next_step").click(function () {
    if(flag==4){

    }else {
        $(".step"+flag).hide();
        flag++;
        $(".step"+flag).show();
        $(".step_nav"+flag).addClass("active_step");
    }
});