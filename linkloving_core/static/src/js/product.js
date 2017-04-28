odoo.define('linkloving_core.product_detail', function (require) {
    "use strict";

    var core = require('web.core');
    var Model = require('web.Model');
    var Widget = require('web.Widget');

    var QWeb = core.qweb;
    var _t = core._t;


    var KioskConfirm = Widget.extend({
        template: "HomePage",
        events: {
            'click .click_tag_a': 'show_bom_line',
            'click .show_po_number':'to_po_page',
        },
        to_po_page:function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var act_id = target.getAttribute("data-id");
            act_id = parseInt(act_id);
            var action = {
                name:"采购订单",
                type: 'ir.actions.act_window',
                res_model:'purchase.order',
                view_type: 'form',
               view_mode: 'tree,form',
                views: [[false, 'form']],

                // tag: 'hr_attendance_kiosk_confirm',
                res_id: act_id,
                target:"new"
                // employee_name: this.record.name.raw_value,
                // employee_state: this.record.attendance_state.raw_value,
            };
            console.log(action);
            this.do_action(action);
        },

        init: function (parent, action) {
            this._super.apply(this, arguments);
            this.product_id = action.product_id;
            var self = this;
        },
        show_bom_line: function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            //若点击的是
            if(target.classList.contains('show_bom_line_one')||target.classList.contains('show_bom_line_two')){
                target = target.parentNode;
                console.log('sss')
            }
            //小三角的变化
            if(target.childNodes.length > 1){
                if(target.childNodes[1].classList.contains("fa-caret-right")){
                    target.childNodes[1].classList.remove("fa-caret-right");
                    target.childNodes[1].classList.add("fa-caret-down");
                }else if(target.childNodes[1].classList.contains("fa-caret-down")){
                    target.childNodes[1].classList.remove("fa-caret-down");
                    target.childNodes[1].classList.add("fa-caret-right");
                }
            }
            if(target.classList.contains('open-sign')){
                if(target.classList.contains("fa-caret-right")){
                    target.classList.remove("fa-caret-right");
                    target.classList.add("fa-caret-down");
                }else if(target.classList.contains("fa-caret-down")){
                    target.classList.remove("fa-caret-down");
                    target.classList.add("fa-caret-right");
                }
                target = target.parentNode;
            }
            if(target.attributes['data-level'] && target.attributes['data-level'].nodeValue=='true'){
                if(target.attributes['data-product-id']){
                     var product_id = target.attributes['data-product-id'].nodeValue;
                        product_id = parseInt(product_id);
                        // console.log(product_id);
                        new Model("product.template")
                            .call("get_detail", [product_id])
                            .then(function (result) {
                                console.log(result);
                                // console.log(self.$("#"+product_id+">.panel-body").html());
                                self.$("#"+product_id+">.panel-body").html(" ");
                                if(result.bom_lines.length>0){
                                    self.$("#"+product_id+">.panel-body").append(QWeb.render('show_bom_line_tr_add', {bom_lines: result.bom_lines,result:result}));
                                }
                                if(result.mo_ids.length>0){
                                    for(var i=0;i<result.mo_ids.length;i++){
                                        result.mo_ids[i].date = result.mo_ids[i].date.substr(0,10);
                                    }
                                    self.$("#"+product_id+">.panel-body").prepend(QWeb.render('show_bom_line_mo',{mo:result.mo_ids}));
                                }
                                 if(result.po_lines.length>0){
                                    for(var i=0;i<result.po_lines.length;i++){
                                        result.po_lines[i].date_planned = result.po_lines[i].date_planned.substr(0,10);
                                    }
                                    self.$("#"+product_id+">.panel-body").prepend(QWeb.render('show_bom_line_po',{po:result.po_lines}));
                                }
                            });
                 }
            }
        },
        start: function () {
            var self = this;
            if(this.product_id){
                return new Model("product.template")
                .call("get_detail", [this.product_id])
                .then(function (result) {
                    console.log(result);
                    self.$el.append(QWeb.render('show_bom_line_tr', {bom_lines: result.bom_lines,result:result}));
                    if(result.mo_ids.length>0){
                        for(var i=0;i<result.mo_ids.length;i++){
                            result.mo_ids[i].date = result.mo_ids[i].date.substr(0,10);
                        }
                        self.$('.panel-body').prepend(QWeb.render('show_bom_line_mo',{mo:result.mo_ids}));
                    }
                    if(result.po_lines.length>0){
                        for(var i=0;i<result.po_lines.length;i++){
                            result.po_lines[i].date_planned = result.po_lines[i].date_planned.substr(0,10);
                        }
                        self.$('.panel-body').prepend(QWeb.render('show_bom_line_po',{po:result.po_lines}));
                    }

                });
            }
        },
    });

    core.action_registry.add('product_detail', KioskConfirm);

    return KioskConfirm;

});