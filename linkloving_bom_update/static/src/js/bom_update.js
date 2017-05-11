/**
 * Created by 123 on 2017/5/10.
 */
odoo.define('linkloving_bom_update.bom_update', function (require) {
    "use strict";

    var core = require('web.core');
    var Model = require('web.Model');
    var Widget = require('web.Widget');

    var QWeb = core.qweb;
    var _t = core._t;

    var BomUpdate = Widget.extend({
        init: function (parent, action) {
            this._super.apply(this, arguments);
            this.bom_id = action.bom_id;
            var self = this;
        },
        start: function () {
            var self = this;
            if (this.bom_id) {
                return new Model("mrp.bom")
                    .call("get_bom", [this.bom_id])
                    .then(function (result) {
                        console.log(result);
                    })
            }
        }


    })

    core.action_registry.add('bom_update', BomUpdate);

    return BomUpdate;
})