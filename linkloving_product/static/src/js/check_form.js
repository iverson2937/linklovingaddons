/**
 * Created by 123 on 2017/7/6.
 */
console.log($(".step2"));
var flag = 1;
$(".pre_step").click(function () {
    if(flag==1){

    }else {
        $(".step"+flag).hide(100);
        flag--;
        $(".step"+flag).show(200);
    }
});
$(".next_step").click(function () {
    if(flag==3){

    }else {
        $(".step"+flag).hide();
        flag++;
        $(".step"+flag).show();
    }
});