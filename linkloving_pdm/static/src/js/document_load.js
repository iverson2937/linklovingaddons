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

        event:{
          'click .load_file_submit':'load_file'
        },
        load_file:function () {
            console.log('1')
		    var filename = document.getElementById("importFile").value;
		    // 这时的filename不是 importFile 框中的值
		    alert(filename);
            console.log('hjhjhj')
            console.log('2')
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