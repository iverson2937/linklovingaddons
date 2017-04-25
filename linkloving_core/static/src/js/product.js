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
            'click .level-top': 'show_bom_line',
        },

        init: function (parent, action) {
            this._super.apply(this, arguments);
            this.product_id = action.product_id;
            var self = this;
        },
        show_bom_line: function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            if (target.classList.contains("fa-caret-right")) {
                target.classList.remove("fa-caret-right");
                target.classList.add("fa-caret-down");
                console.log(target.parentNode.getAttribute("data-id"));

                $(".tr_level_top").show();
            } else if (target.classList.contains("fa-caret-down")) {
                target.classList.remove("fa-caret-down");
                target.classList.add("fa-caret-right");
                $(".tr_level_top").hide();
            }

        },
        start: function () {
            var self = this;
            return new Model("product.template")
                .call("get_detail", [this.product_id])
                .then(function (result) {
                    console.log(result.bom_lines.length);
                    if(result.bom_lines.length!=0){
                        self.$(".bodys").append(QWeb.render('show_bom_line_tr', {bom_lines: result.bom_lines}));
                    }else {
                        self.$(".petstore_table").hide();
                    }
                    self.$(".show_product_name").html(result.name)
                });

        },
    });

    core.action_registry.add('product_detail', KioskConfirm);

    return KioskConfirm;

});
