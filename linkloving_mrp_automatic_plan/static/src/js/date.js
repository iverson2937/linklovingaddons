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
          'click .next': 'get_holiday'
        },
        get_holiday:function () {
            var self = this;
            $("#id_container .left ol li").each(function () {
                $(this).children(".holiday").remove();
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
        },
        start: function () {
            var self = this;
            return new Model("linkloving_mrp_automatic_plan.linkloving_mrp_automatic_plan")
                .call("get_holiday", [""])
                .then(function (result){
                    console.log(result)
                    var holiday_jsons = JSON.parse(result.holiday)
                    var holidays = holiday_jsons.data[0].holiday;
                    console.log(holidays)
                    self.holidays = holidays

                    self.$el.append(QWeb.render('Date_Detail'))

                    setTimeout(function () {
                        console.log(document.getElementById("GD12"))
                        $(holidays).each(function () {
                            console.log($(this.list))
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