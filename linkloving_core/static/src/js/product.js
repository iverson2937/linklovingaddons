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
            'click .level-top': 'zhankai',
        },
        zhankai: function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            if (target.classList.contains("fa-caret-right")) {
                console.log(target.className);
                target.classList.remove("fa-caret-right");
                target.classList.add("fa-caret-down");
                $(".ceshi").show()
            } else if (target.classList.contains("fa-caret-down")) {
                target.classList.remove("fa-caret-down");
                target.classList.add("fa-caret-right");
                $(".ceshi").hide()
            }

        },
        start: function () {
            // return $.when(
            // new local.PetToysList(this).appendTo(this.$('.oe_petstore_homepage_left')),
            // new local.MessageOfTheDay(this).appendTo(this.$('.oe_petstore_homepage_right')),
            // new local.OpenTheTree(this).appendTo(this.$(".oe_petstore_homepage_right"))
            // );

            var self = this;
            return new Model("product.template")
                .call("get_detail", [{'partner_id': 'ssss'}])
                .then(function (result) {
                    console.log(result)
                    _(result).each(function (items) {
                        self.$(".bodys").append(QWeb.render('xx', {items: items}));
                    })
                });

        },
    });

    core.action_registry.add('product_detail', KioskConfirm);

    return KioskConfirm;

});
