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
            // 'blur .origin_bom input':'confirm_origin_bom_sel_func',
            'click .origin_bom ul li':'confirm_origin_bom_sel_func'
        },

        //确认源bom的选择 渲染table表
        confirm_origin_bom_sel_func:function () {
            var bom_id = $('.origin_bom select option:selected').attr('data-bom-id');
            new Model('mrp.bom').call('get_bom_line_list', [[parseInt(bom_id)]]).then(function (result) {
                console.log(result);
                $('.cost_matching_container tbody').html('');
                $('.cost_matching_container tbody').append(QWeb.render('cost_matching_tbody_templ',{result:result}));
            })
        },
        //源bom下的输入框搜索事件
        origin_bom_search_func: _.debounce (function(ev) {
            new Model('mrp.bom').call('get_bom_list', [{name: $('.origin_bom input').val()}]).then(function (result) {
                console.log(result);
                $('.origin_bom select').html('');
                $.when($('.origin_bom select').append(QWeb.render('cost_matching_select_templ',{result:result}))).then(function () {
                     $('.origin_bom select').selectpicker('refresh')
                })
            })
        },300,true),

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
