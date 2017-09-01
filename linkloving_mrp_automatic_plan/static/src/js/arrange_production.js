/**
 * Created by 123 on 2017/8/31.
 */
odoo.define('linkloving_mrp_automatic_plan.arrange_production', function (require) {
    "use strict";

    var core = require('web.core');
    var Model = require('web.Model');
    var Widget = require('web.Widget');

    var QWeb = core.qweb;
    var _t = core._t;

    var Arrange_Production = Widget.extend({
        template: 'arrange_production_tmp',
        events:{
          'mousedown .ap_item_wrap': 'ap_mousedown_event',
          // 'mousemove .ap_item_wrap': 'ap_mousemove_event'

        },
        // ap_mousemove_event:function (e) {
        //     console.log('kkkkkkkk')
        //     $(cloned).stop();//加上这个之后
        //
        //     var _x = ev.pageX - x;//获得X轴方向移动的值
        //     var _y = ev.pageY - y;//获得Y轴方向移动的值
        //
        //     $(cloned).animate({left:_x+"px",top:_y+"px"},0);
        // },
        ap_mousedown_event:function (e) {
            $(document).unbind('mousemove');
            $(document).unbind('mouseup');
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var more_width = $(".o_sub_menu")[0].clientWidth;
            var more_height = $('.navbar-collapse')[0].clientHeight;

            var offset = $(target).offset();//DIV在页面的位置
            var x = e.pageX - offset.left;//获得鼠标指针离DIV元素左边界的距离
            var y = e.pageY - offset.top+10;//获得鼠标指针离DIV元素上边界的距离

            console.log($(target).index());
            var select = $(target)   //被选中的节点

            var cloned = $(target).clone(true).appendTo('body');
            $(cloned).addClass('cloned_div');

            $(cloned).css({
                'position':'absolute',
                'left': e.pageX - x +'px',
                'top': e.pageY - y +'px',
                'width': target.offsetWidth + 'px'
            });
            $(select).css('visibility','hidden');

            $(document).bind("mousemove",function(ev){ //绑定鼠标的移动事件，因为光标在DIV元素外面也要有效果，所以要用doucment的事件，而不用DIV元素的事件
                $(cloned).stop();//加上这个之后
                var _x = ev.pageX - x;//获得X轴方向移动的值
                var _y = ev.pageY - y;//获得Y轴方向移动的值

                $(cloned).animate({left:_x+"px",top:_y+"px"},0);
            });

            $(document).bind("mouseup",function (ev,e) {
                var right = $("#a_p_right")[0];
	        	var left = $("#a_p_left")[0];
                 var e = e || window.event;
                var target = e.target || e.srcElement;
                console.log(ev);

                if(typeof right == 'undefined' || typeof left == 'undefined'){
                    return
                }
	            $(this).unbind("mousemove");
                $(cloned).css('top','-200px');
                $(cloned).css('display','none');

                console.log(document.elementFromPoint(e.pageX,e.pageY))
                this.append_target = document.elementFromPoint(e.pageX,e.pageY);
                console.log($(this.append_target)[0].className);
                if($(this.append_target)[0].className != 'production_lists_wrap'){
                    console.log($(this.append_target).parents('.production_lists_wrap'));
                    var x = $(this.append_target).parents('.production_lists_wrap')
                     $(cloned).appendTo($(x));
                    $(cloned).css('display','block');
                    $(cloned).css('width','90%');
                    $(cloned).css('position','static');
                    $(select).remove();
                }else {
                    // $(cloned).appendTo($(this.append_target));
                    $(cloned).css('display','block');
                    $(cloned).css('width','90%');
                    $(cloned).css('position','static');
                    $(select).remove();
                }

	            // console.log(document.elementFromPoint(e.pageX,e.pageY))
            })

        },

        init: function (parent, action) {
            this._super.apply(this, arguments);
            var self = this;
        },
        start: function () {
            var self = this;
        }

    })

    core.action_registry.add('arrange_production', Arrange_Production);

    return Arrange_Production;
})
