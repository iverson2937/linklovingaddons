/**
 * Created by 123 on 2017/7/26.
 */
/**
 * Created by 123 on 2017/7/10.
 */
odoo.define('linkloving_purchase.mo_ques', function (require) {
    "use strict";

    var core = require('web.core');
    var Model = require('web.Model');
    var Widget = require('web.Widget');
    var View = require('web.View');
    var Dialog = require('web.Dialog');
    var ControlPanelMixin = require('web.ControlPanelMixin');
    var SearchView = require('web.SearchView');
    var data = require('web.data');
    var _t = core._t;


    var MoQuestion = Widget.extend({
        template: '',
        events: {

        },
        init: function (parent, action) {
            this._super.apply(this, arguments);
        },
        start: function () {
            var self = this;

        }
    });
    core.action_registry.add('mo_ques', MoQuestion);

    return MoQuestion;
});