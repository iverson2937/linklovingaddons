/**
 * Created by 123 on 2017/5/10.
 */
odoo.define('linkloving_pdm.document_manage', function (require) {
    "use strict";

    var core = require('web.core');
    var Model = require('web.Model');
    var Widget = require('web.Widget');

    var QWeb = core.qweb;
    var _t = core._t;

    var DocumentManage = Widget.extend({
        template: 'document_load_page',
        events:{
            'show.bs.tab .tab_toggle_a':'document_change_tabs',
            'click .document_manage_btn':'document_form_pop'
        },
        document_form_pop:function (e) {
            var e = e||window.event;
            var target = e.target||e.srcElement;
            var file_id = $(target).attr("data-id");
            var action = {
                name:"详细",
                type: 'ir.actions.act_window',
                res_model:'review.process.wizard',
                view_type: 'form',
                view_mode: 'tree,form',
                views: [[false, 'form']],
                context: {'default_product_attachment_info_id':file_id} ,
                target:"new"
            };
            this.do_action(action);
        },
        document_change_tabs:function (e) {
            var e = e||window.event;
            var target = e.target||e.srcElement;
            var file_type = $(target).attr("data");
            return new Model("product.template")
                .call("get_attachemnt_info_list", [this.product_id], {type:file_type})
                .then(function (result) {
                    console.log(result);
                    self.$("#"+file_type).html("");
                    self.$("#"+file_type).append(QWeb.render('active_document_tab', {result: result}));
                })
        },
        init: function (parent, action) {
            this._super.apply(this, arguments);
            this.product_id = action.product_id;
            var self = this;
        },
        start: function () {
            var self = this;
            return new Model("product.template")
                .call("get_file_type_list", [this.product_id])
                .then(function (result) {
                    console.log(result);
                    self.$el.append(QWeb.render('document_load_detail', {result: result}));
                })
        }


    })

    core.action_registry.add('document_manage', DocumentManage);

    return DocumentManage;
})