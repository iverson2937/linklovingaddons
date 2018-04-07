/**
 * Created by allen on 2018/04/04.
 */
odoo.define('linkloving_process_inherit.bom_cost_reproduce', function (require) {
    "use strict";

    var core = require('web.core');
    var Model = require('web.Model');
    var Widget = require('web.Widget');
    var data = require('web.data');
    var ControlPanelMixin = require('web.ControlPanelMixin');
    var pyeval = require('web.pyeval');
    var QWeb = core.qweb;
    var BomCostReproduce = Widget.extend(ControlPanelMixin, {
        template: "cost_matching_templ",
        events: {
            'input .origin_bom input': 'origin_bom_search_func',
        },

        origin_bom_search_func: _.debounce (function(ev) {
            new Model('mrp.bom').call('get_bom_list', [[],{name:$('.origin_bom input').val()}]).then(function (result) {
                console.log(result);
            })
        },1000,true),

        init:function (parent, action) {
            this._super(parent);
            this._super.apply(this, arguments);
        },
        start:function () {

        },

    });

    core.action_registry.add('bom_cost_reproduce', BomCostReproduce);

    return BomCostReproduce;


});
