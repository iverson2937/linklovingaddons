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
            'click .show_mo_number': 'to_mo_page',
            'click .chk_all': 'check_all',
            'click .chk_all_mo': 'check_all',
            'click .send-po-btn':'get_po_id',
            'click .send-mo-btn':'get_mo_id',
        },
        check_all:function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var chk_id = target.getAttribute("id");
            var abc=$("input[name="+chk_id+"]");
            abc.each(function () {
                $(this).prop("checked",target.checked)
            })
        },
        get_po_id:function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var check_name =  target.getAttribute("check-name");
            // console.log(check_name);
            var merge_inputs_ids = [];
            var merge_inputs = $("input[name="+check_name+"]");
            merge_inputs.each(function () {
                if($(this).prop("checked")){
                    merge_inputs_ids.push(parseInt($(this).attr("po-id")))
                }
            })
            console.log(merge_inputs_ids)
             new Model("product.template").call("action_combine",[merge_inputs_ids]).then(function (result) {
                 console.log(result);
             })
        },
        get_mo_id:function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var check_name =  target.getAttribute("check-name");
            var mo_merge_inputs_ids = [];
            var mo_merge_inputs = $("input[name="+check_name+"]");
            mo_merge_inputs.each(function () {
                if($(this).prop("checked")){
                    mo_merge_inputs_ids.push(parseInt($(this).attr("mo-id")))
                }
            });
            console.log(mo_merge_inputs_ids);
            new Model("product.template").call("action_combine", [mo_merge_inputs_ids]).then(function (result) {
                console.log(result);
            })
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
                res_id: act_id,
                target:"new"
                // employee_name: this.record.name.raw_value,
                // employee_state: this.record.attendance_state.raw_value,
            };
            this.do_action(action);
        },
        to_mo_page:function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var act_id = target.getAttribute("data-id");
            act_id = parseInt(act_id);
            var action = {
                name:"制造单",
                type: 'ir.actions.act_window',
                res_model:'mrp.production',
                view_type: 'form',
               view_mode: 'tree,form',
                views: [[false, 'form']],
                res_id: act_id,
                target:"new"
            };
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
            // if(target.attributes['data-level'] && target.attributes['data-level'].nodeValue=='true'){
                if(target.attributes['data-product-id']){
                     var product_id = target.attributes['data-product-id'].nodeValue;
                     var transform_service="";
                        product_id = parseInt(product_id);
                        // console.log(product_id);
                        new Model("product.template")
                            .call("get_detail", [product_id])
                            .then(function (result) {
                                console.log(result);
                                var po_length = result.po_lines.length;
                                var bom_length = result.bom_lines.length;
                                var mo_length = result.mo_ids.length;
                                self.$("#"+product_id+">.panel-body").html(" ");
                                 if(result.po_lines.length>0){
                                    for(var i=0;i<result.po_lines.length;i++){
                                        result.po_lines[i].date_planned = result.po_lines[i].date_planned.substr(0,10);
                                    }
                                }
                                if(result.mo_ids.length>0){
                                    for(var i=0;i<result.mo_ids.length;i++){
                                        result.mo_ids[i].date = result.mo_ids[i].date.substr(0,10);
                                    }
                                }
                                var service={
                                    'ordering':'订单制',
                                    'stock':'备货制'
                                }
                                if(result.service=='ordering'){
                                    result.service='订单制'
                                }else if(result.service=='stock'){
                                    result.service='备货制'
                                }
                                if(result.type == '半成品'){
                                    result.service='备货制';
                                }
                                for(var i=0;i<result.bom_lines.length;i++){
                                    if(result.bom_lines[i].type=='半成品'){
                                        result.bom_lines[i].service='备货制';
                                    }
                                    if(result.bom_lines[i].service=='ordering'){
                                        result.service='订单制'
                                    }else if(result.service=='stock'){
                                        result.bom_lines[i].service='备货制'
                                    }
                                }

                                self.$("#"+product_id+">.panel-body").append(QWeb.render('show_bom_line_tr_add', {bom_lines: result.bom_lines,result:result,po_length:po_length,bom_length:bom_length,mo_length: mo_length,service:service}));
                            });
                 }
            // }
        },
        start: function () {
            var self = this;
            if(this.product_id){
                return new Model("product.template")
                .call("get_detail", [this.product_id])
                .then(function (result) {
                    console.log(result);
                    var transform_service="";
                    var po_length = result.po_lines.length;
                    var bom_length = result.bom_lines.length;
                    var mo_length = result.mo_ids.length;
                    //时间截取
                    if(result.mo_ids.length>0){
                        for(var i=0;i<result.mo_ids.length;i++){
                            result.mo_ids[i].date = result.mo_ids[i].date.substr(0,10);
                        }
                    }
                    if(result.po_lines.length>0){
                        for(var i=0;i<result.po_lines.length;i++){
                            result.po_lines[i].date_planned = result.po_lines[i].date_planned.substr(0,10);
                        }
                    }
                    var service={
                        'ordering':'订单制',
                        'stock':'备货制'
                    }
                    if(result.service=='ordering'){
                        result.service='订单制'
                    }else if(result.service=='stock'){
                        result.service='备货制'
                    }
                    if(result.type == '半成品'){
                        result.service='备货制';
                    }
                    for(var i=0;i<result.bom_lines.length;i++){
                        if(result.bom_lines[i].type=='半成品'){
                            result.bom_lines[i].service='备货制';
                        }
                        if(result.bom_lines[i].service=='ordering'){
                            result.service='订单制'
                        }else if(result.service=='stock'){
                            result.bom_lines[i].service='备货制'
                        }
                    }
                    self.$el.append(QWeb.render('show_bom_line_tr', {bom_lines: result.bom_lines,result:result,po_length:po_length,bom_length:bom_length,mo_length: mo_length,service:service}));

                });
            }
        },
    });

    core.action_registry.add('product_detail', KioskConfirm);

    return KioskConfirm;

});
