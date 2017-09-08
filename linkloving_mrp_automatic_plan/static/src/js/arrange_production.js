/**
 * Created by 123 on 2017/8/31.
 */
odoo.define('linkloving_mrp_automatic_plan.arrange_production', function (require) {
    "use strict";

    var core = require('web.core');
    var Model = require('web.Model');
    var Widget = require('web.Widget');
    var data = require('web.data');
    var common = require('web.form_common');
    var framework = require('web.framework');
    var datepicker = require('web.datepicker');
    var QWeb = core.qweb;
    var _t = core._t;
    var myself;

    var Arrange_Production = Widget.extend({
        template: 'arrange_production_tmp',
        events:{
          'mousedown .a_p_move_point': 'ap_mousedown_event',
          'click .a_p_showorhide': 'production_lists_wrap_toggle',
          'click .to_bom': 'to_bom_func',
        },
        to_bom_func:function (e) {
             var e = e || window.event;
             var target = e.target || e.srcElement;
             var action = {
               'type': 'ir.actions.client',
                'tag': 'new_bom_update',
                'bom_id': parseInt($(target).parents('.ap_item_wrap').attr("data-bom-id")),
                'is_show': false,
                'target':'new'
            };
            this.do_action(action);
        },
        production_lists_wrap_toggle:function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            $(target).parents('.production_line').next('.production_lists_wrap').slideToggle("fast");
            if($(target).hasClass('fa-chevron-down')){
                $(target).removeClass('fa-chevron-down');
                $(target).addClass('fa-chevron-up');
                var index = $(target).parents('.production_line').attr("data-index");

                new Model("mrp.production.line")
                    .call("get_mo_by_productin_line", [[]], {production_line_id: myself.mydataset.product_line[index].id,limit:10,offset:0, planned_date:myself.chose_date})
                    .then(function (result) {
                        console.log(result);
                        // myself.mydataset = result;
                        $(target).parents('.production_line').next('.production_lists_wrap').html("");
                        $(target).parents('.production_line').next('.production_lists_wrap').append(QWeb.render('a_p_render_right_tmpl',{result: result}));
                    })

            }else {
                $(target).removeClass('fa-chevron-up');
                $(target).addClass('fa-chevron-down');
            }
        },

        ap_mousedown_event:function (e) {
            if(e.button == 2){
                return false;
            }
            $(document).unbind('mousemove');
            $('.a_p_move_point').unbind('mouseup');
            var e = e || window.event;
            var target = e.target || e.srcElement;
            if($(target).parents('.ap_item_wrap').length>=1){
                target = $(target).parents('.ap_item_wrap')[0]
            }else {
                return
            }

            var offset = $(target).offset();//DIV在页面的位置
            var x = e.pageX - offset.left;//获得鼠标指针离DIV元素左边界的距离
            var y = e.pageY - offset.top+10;//获得鼠标指针离DIV元素上边界的距离

            var start_x = e.pageX;
            var start_y = e.pageY;

            var select = $(target);   //被选中的节点

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
                if(ev.button == 2){
                    return false;
                }

                $(cloned).stop();//加上这个之后
                var _x = ev.pageX - x;//获得X轴方向移动的值
                var _y = ev.pageY - y;//获得Y轴方向移动的值

                $(cloned).animate({left:_x+"px",top:_y+"px"},0);
            });

            $('.a_p_move_point').bind("mouseup",function (ev) {
                if(ev.button == 2){
                    return false;
                }
                if(ev.pageX == start_x && ev.pageY == start_y){
                    $(cloned).remove();
                    $(select).css('visibility','visible');
                    return;
                }

                var right = $("#a_p_right")[0];
	        	var left = $("#a_p_left")[0];

                if(typeof right == 'undefined' || typeof left == 'undefined'){
                    return
                }
	            $(this).unbind("mousemove");
                $(cloned).css('top','-200px');
                $(cloned).css('display','none');
                ev.preventDefault();
                console.log(document.elementFromPoint(ev.pageX,ev.pageY));
                this.append_target = document.elementFromPoint(ev.pageX,ev.pageY);
                console.log($(this.append_target)[0].className);
                if($(this.append_target)[0].className != 'production_lists_wrap'){
                    if($(this.append_target).parents('.production_lists_wrap').length>=1){
                         var x = $(this.append_target).parents('.production_lists_wrap');
                         $(select).appendTo($(x));
                         $(select).css('visibility','visible');
                         $(cloned).remove();
                         var mo_id = $(select).attr('data-mo-id');
                         var pt_line_index = $(x).prev('.production_line').attr('data-index');
                         myself.no_ap_to_ag(parseInt(mo_id), myself.mydataset.product_line[pt_line_index].id);
                    }else if($(this.append_target).parents('#a_p_right').length>=1){
                        var x = $(this.append_target).parents('#a_p_right');
                        var mo_id = $(select).attr('data-mo-id');
                        $(select).appendTo($(x));
                        $(select).css('visibility','visible');
                        $(cloned).remove();
                        myself.no_ap_to_ag(parseInt(mo_id),false);
                    }else if($(this.append_target).attr('id') == 'a_p_right'){
                        var x = $('#a_p_right');
                        var mo_id = $(select).attr('data-mo-id');
                        $(select).appendTo($(x));
                        $(select).css('visibility','visible');
                        $(cloned).remove();
                        myself.no_ap_to_ag(parseInt(mo_id),false);
                    }
                    else {
                         console.log('其他情况')
                         $(cloned).remove();
                         $(select).css('visibility','visible')
                    }
                }
                else {
                    $(select).appendTo($(this.append_target));
                    $(select).css({
                        "width":"95%",
                        "position":"static",
                        "visibility":"visible"
                    });
                    $(cloned).remove();
                    var mo_id = $(select).attr("data-mo-id");
                    var pt_line_index = $(this.append_target).prev('.production_line').attr('data-index');
                    myself.no_ap_to_ag(parseInt(mo_id), myself.mydataset.product_line[pt_line_index].id);
                }

            })

        },
        no_ap_to_ag: function (mo_id,production_line_id) {
              framework.blockUI();
              new Model("mrp.production")
                    .call("settle_mo", [mo_id], {production_line_id:production_line_id,settle_date:myself.chose_date})
                    .then(function (result) {
                        console.log(result);
                        framework.unblockUI();
                    })
        },
        build_widget: function() {
            return new datepicker.DateWidget(this);
        },
        init_date_widget:function (node) {
             var self = this;
            this.datewidget = this.build_widget();
            this.datewidget.on('datetime_changed', this, function() {
                myself.chose_date = self.datewidget.get_value();
                $(".bootstrap-datetimepicker-widget").attr('id','a_p_date');
                $(".a_p_showorhide").each(function () {
                    if($(this).hasClass('fa-chevron-up')){
                        $(this).parents('.production_line').next('.production_lists_wrap').slideToggle("fast");
                        $(this).removeClass('fa-chevron-up');
                        $(this).addClass('fa-chevron-down');
                    }
                })
            });
            this.datewidget.appendTo(node).done(function() {
                self.setupFocus(self.datewidget.$input);
                self.datewidget.set_datetime_default();
                self.datewidget.commit_value();
            });
        },
        //右边未排产的接口
        un_arrange_production:function (process_id,limit,offset) {
            framework.blockUI();
            new Model("mrp.production")
                    .call("get_unplanned_mo", [[]], {process_id:process_id,limit:limit,offset:offset})
                    .then(function (result) {
                        console.log(result);
                        myself.mydataset.mo = result;
                        $("#a_p_right").html('');
                        $("#a_p_right").append(QWeb.render('a_p_render_right_tmpl',{result: result}));
                        framework.unblockUI();
                    })
        },
        init: function (parent, action) {
            this._super.apply(this, arguments);
            var self = this;
            if (action.process_id) {
                this.process_id = action.process_id;
            } else {
                this.process_id = action.params.active_id;
            }
        },
        setupFocus: function ($e) {
            var self = this;
            $e.on({
                focus: function () {
                    self.trigger('focused');
                },
                blur: function () { self.trigger('blurred'); }
            });
        },
        start: function () {
            var self = this;
            myself = this;
            myself.mydataset = {};
            framework.blockUI();
            new Model("mrp.production.line")
                    .call("get_production_line_list", [[]], {process_id:this.process_id})
                    .then(function (result) {
                        console.log(result);
                        myself.mydataset.product_line = result;
                        self.$el.eq(0).append(QWeb.render('a_p_render_tmpl', {result: result}));
                        self.init_date_widget($(".a_p_time_start"));
                        framework.unblockUI();
                    })
            //未排产
            self.un_arrange_production(this.process_id,10,0);
        }

    })

    core.action_registry.add('arrange_production', Arrange_Production);

    return Arrange_Production;
})
