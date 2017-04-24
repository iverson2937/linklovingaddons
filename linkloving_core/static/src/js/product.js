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
        show_bom_line: function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            if (target.classList.contains("fa-caret-right")) {
                console.log(target.className);
                target.classList.remove("fa-caret-right");
                target.classList.add("fa-caret-down");
                $(".tr_level_top").show()
            } else if (target.classList.contains("fa-caret-down")) {
                target.classList.remove("fa-caret-down");
                target.classList.add("fa-caret-right");
                $(".tr_level_top").hide()
            }

        },
        start: function () {
            var self = this;
            return new Model("product.template")
                .call("get_detail", [54115])
                .then(function (result) {
                    self.$(".bodys").append(QWeb.render('show_bom_line_tr', {items: result}));
                    self.$(".show_product_name").html(result.name)

                });

        },
    });

    core.action_registry.add('product_detail', KioskConfirm);

    return KioskConfirm;

});
