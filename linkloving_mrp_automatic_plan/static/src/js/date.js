/**
 * Created by 123 on 2017/5/10.
 */
odoo.define('linkloving_mrp_automatic_plan.date_manage', function (require) {
    "use strict";

    var core = require('web.core');
    var Model = require('web.Model');
    var Widget = require('web.Widget');

    var QWeb = core.qweb;
    var _t = core._t;

    var DateManage = Widget.extend({
        template: 'Date_Container',
        events:{
          'click .prev': 'get_holiday',
          'click .next': 'get_holiday',
          'click .date_edit_x': 'edit_status_x',
          'click .date_save_x': 'edit_save_x',
          'click .date_day': 'edit_day',
          'click .edit_holiday': 'edit_to_holiday',
          'click .edit_work': 'edit_to_work',
          'click .date_edit_x_cancel': 'cancel_edit'
        },
        cancel_edit:function () {
            var self = this;
            self.edit_status = false;
            $(".date_save_x").text("编辑");
            $(".date_save_x").addClass("date_edit_x");
            $(".date_save_x").removeClass("date_save_x");
            $(".date_edit_x_cancel").hide();
        },
        //编辑选择放假
        edit_to_holiday:function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var self = this;
            console.log(self.holidays);
            //放假的效果
            $(target).parents(".date_day").append("<div class='holiday'>假</div>");
            //编辑界面消失
            $(target).parents(".date_day").children(".date_edit_condition").hide();
            //将选择的放假的日子保存到self.holidays里
            var detail_edit_day = $(target).parents(".date_day").attr("data-complete");
            var edit_new_holiday = {
                "list":[{
                    "date": detail_edit_day,
                    "status":"1"
                }]
            }
            self.holidays.push(edit_new_holiday);
        },
        //编辑选择上班
        edit_to_work:function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var self = this;
            console.log(self.holidays);
            //放假的效果
            $(target).parents(".date_day").append("<div class='work'>班</div>");
            //编辑界面消失
            $(target).parents(".date_day").children(".date_edit_condition").hide();
            //将选择的放假的日子保存到self.holidays里
            var detail_edit_day = $(target).parents(".date_day").attr("data-complete");
            var edit_new_holiday = {
                "list":[{
                    "date": detail_edit_day,
                    "status":"2"
                }]
            }
            self.holidays.push(edit_new_holiday);
        },
        edit_day:function (e) {
            var self = this;
            var e = e || window.event;
            var target = e.target || e.srcElement;
            if(self.edit_status == true){
                if($(target).hasClass("layer")||$(target).hasClass("border")||$(target).hasClass("solar")||$(target).hasClass("lunar")){
                    target = $(target).parent()
                }else {
                    target = $(target)
                }
                target.children(".date_edit_condition").show();
            }

        },
        //保存时的事件  后期加上 回传给后台编辑的数据 的代码
        edit_save_x:function () {
            var self = this;
            self.edit_status = false;
            $(".date_save_x").text("编辑");
            $(".date_save_x").addClass("date_edit_x");
            $(".date_save_x").removeClass("date_save_x");
            $(".date_edit_x_cancel").hide()
        },
        //点击编辑的事件
        edit_status_x:function () {
            var self = this;
            self.edit_status = true;
            $(".date_edit_x").text("保存");
            $(".date_edit_x").addClass("date_save_x");
            $(".date_edit_x").removeClass("date_edit_x");
            $(".date_edit_x_cancel").css("display","inline-block");
        },
        get_holiday:function () {
            var self = this;
            $("#id_container .left ol li").each(function () {
                $(this).children(".holiday").remove();
                $(this).children(".date_edit_condition").hide();
                $(this).children(".work").remove();
            })
            $(self.holidays).each(function () {
                $(this.list).each(function () {
                    if(this.status==1){
                        if($("#id_container .left ol li[data-complete="+this.date+"] .solar").text()!=""){
                            $("#id_container .left ol li[data-complete="+this.date+"]").append("<div class='holiday'>假</div>");
                        }
                    }else {
                        if($("#id_container .left ol li[data-complete="+this.date+"] .solar").text()!=""){
                            $("#id_container .left ol li[data-complete="+this.date+"]").append("<div class='work'>班</div>");
                        }
                    }
                })
            })

        },
        init: function (parent, action) {
            this._super.apply(this, arguments);
            // this.product_id = action.product_id;
            var self = this;
            self.edit_status = false;
            // self.ceshi = "canghaiyeumimgzhuyoulei";
        },
        start: function () {
            var self = this;
            return new Model("linkloving_mrp_automatic_plan.linkloving_mrp_automatic_plan")
                .call("get_holiday", [""])
                .then(function (result){
                    console.log(result)
                    var holiday_jsons = JSON.parse(result.holiday)
                    var holidays = holiday_jsons.data[0].holiday;
                    self.holidays = holidays;

                    self.$el.append(QWeb.render('Date_Detail'))

                    setTimeout(function () {
                        $(holidays).each(function () {
                            // console.log($(this.list))
                            $(this.list).each(function () {
                                // console.log(this.date)
                                $("#id_container .left ol li[data-complete="+this.date+"]").css("background","red")
                            })
                        })
                    },200)

                });
        }

    })

    core.action_registry.add('date_manage', DateManage);

    return DateManage;
})