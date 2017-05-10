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

    })

    core.action_registry.add('bom_update', BomUpdate);

    return BomUpdate;
})