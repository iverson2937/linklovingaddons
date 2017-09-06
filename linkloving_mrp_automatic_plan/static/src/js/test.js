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
    var move_id;

    var Arrange_Production = Widget.extend({
        template: 'arrange_production_tmp',
        events:{
            'click .a_p_showorhide': 'production_lists_wrap_toggle',
            'mouseenter .a_p_move_point':'change_drag_true',
            'mouseleave .a_p_move_point':'change_drag_false',
            'dragover #a_p_left':'prevent_default',
            'drop #a_p_left':'move_over_left',
            'dragover #a_p_right':'prevent_default',
            'drop #a_p_right':'move_over_right',
            'dragstart .ap_item_wrap': 'move_start'
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
        move_start:function (ev) {
            var ev = ev || window.event;
            var target = ev.target || ev.srcElement;
            move_id = target.id;
        },
        move_over_left:function (ev) {
            ev.preventDefault();
            var elem = document.getElementById(move_id); //当前拖动的元素
            var toElem = ev.target;
            console.log(toElem.className);
            if(toElem.className == 'ap_item_wrap'){
                $(elem).insertBefore($(toElem));
                var mo_id = $(elem).attr("data-mo-id");
                var pt_line_index = $(toElem).parents('.production_lists_wrap').prev('.production_line').attr('data-index');
                myself.no_ap_to_ag(parseInt(mo_id), myself.mydataset.product_line[pt_line_index].id);
            }else if($(toElem).parents('.ap_item_wrap').length>=1){
                $(elem).insertBefore($(toElem).parents('.ap_item_wrap'));
                var mo_id = $(elem).attr("data-mo-id");
                var pt_line_index = $(toElem).parents('.production_lists_wrap').prev('.production_line').attr('data-index');
                myself.no_ap_to_ag(parseInt(mo_id), myself.mydataset.product_line[pt_line_index].id);
            }
            else if(toElem.className == 'production_lists_wrap'){
                $(toElem).prepend($(elem));
                var mo_id = $(elem).attr("data-mo-id");
                var pt_line_index = $(toElem).prev('.production_line').attr('data-index');
                myself.no_ap_to_ag(parseInt(mo_id), myself.mydataset.product_line[pt_line_index].id);
            }
        },
        move_over_right:function (ev) {
            ev.preventDefault();
            var elem = document.getElementById(move_id); //当前拖动的元素
            var toElem = ev.target;
            console.log(toElem.className);
            if(toElem.className == 'ap_item_wrap'){
                $(elem).insertBefore($(toElem));
                var mo_id = $(elem).attr("data-mo-id");
                myself.no_ap_to_ag(parseInt(mo_id),false);
            }else if($(toElem).parents('.ap_item_wrap').length>=1){
                $(elem).insertBefore($(toElem).parents('.ap_item_wrap'));
                var mo_id = $(elem).attr("data-mo-id");
                myself.no_ap_to_ag(parseInt(mo_id),false);
            }else if($(toElem).attr('id') == 'a_p_right'){
                $(toElem).prepend($(elem));
                var mo_id = $(elem).attr("data-mo-id");
                myself.no_ap_to_ag(parseInt(mo_id),false);
            }
        },
        change_drag_true:function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            $(target).parents('.ap_item_wrap').attr('draggable','true');
        },
        change_drag_false:function () {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            $(target).parents('.ap_item_wrap').attr('draggable','false');
        },
        prevent_default:function (ev) {
            ev.preventDefault(); //阻止向上冒泡
        },

        //拖动的接口
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
        init: function (parent, action) {
            this._super.apply(this, arguments);
            var self = this;
            if (action.process_id) {
                this.process_id = action.process_id;
            } else {
                this.process_id = action.params.active_id;
            }
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
