/**
 * Created by 123 on 2017/6/26.
 */
odoo.define('linkloving_approval.approval_core', function (require){
    "use strict";

    var core = require('web.core');
    var Model = require('web.Model');
    var Widget = require('web.Widget');

    var QWeb = core.qweb;
    var _t = core._t;

    var Approval = Widget.extend({
        template:'approval_load_page',
        init: function (parent, action) {
            this._super.apply(this, arguments);
            if (action.product_id) {
                this.product_id = action.product_id;
            } else {
                this.product_id = action.params.active_id;
            }
            var self = this;
        },
        start: function () {
            var self = this;
            // console.log($("body"))

            self.$el.append(QWeb.render('approval_load_detail'));
            var model = new Model("approval.center");
            //var info_model = new Model("product.attachment.info")
            model.call("fields_get", ["", ['type']]).then(function (result) {
                console.log(result.type);

            })
            return model.call("create", [{res_model: 'product.attachment.info', type: 'waiting_submit'}])
                .then(function (result) {
                    model.call('get_attachment_info_by_type', [result])
                        .then(function (result) {
                            console.log(result)
                        })
                })
        }
    });

    core.action_registry.add('approval_core', Approval);

    return Approval;

})