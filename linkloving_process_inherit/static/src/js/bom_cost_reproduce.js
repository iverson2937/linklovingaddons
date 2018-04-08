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
            'click .add_tr': 'add_tr_func',
            'click .alia_cancel': 'alia_cancel_func',
            'input .origin_bom input': 'origin_bom_search_func',
            // 'blur .origin_bom input':'confirm_origin_bom_sel_func',
            'click .origin_bom ul li': 'confirm_origin_bom_sel_func',
            'click .confirm_sel': 'confirm_sel_func',
            'input .target_bom input': 'origin_bom_search_func',
            'click .target_bom ul li': 'confirm_target_bom_sel_func',
            'click .replace': 'replace_func',
            'click .btn_wrap .save': 'save_func',
            'click .sel_action': 'sel_action_func',
        },
        add_tr_func: function (e) {
            var self = this;

            var e = e || window.event;
            var target = e.target || e.srcElement;
            var bom_line_id = $('.unlock_condition').attr('data-id');


            new Model('mrp.bom.line').call('add_action_line_data', [parseInt(bom_line_id)]).then(function (results) {
                if (results){
                    $('#action_table tbody').append(QWeb.render('add_tr_templ', {'result': results}));
                }



            })
        },
        alia_cancel_func: function () {
            $('.unlock_condition').hide()
        },
        confirm_sel_func: function () {
            var self = this;
            var bom_line_id = $('.unlock_condition').attr('data-id');
            var trs = $('.unlock_condition').find('tr');
            var actions = [];

            function isInteger(obj) {
                return obj % 1 === 0
            }

            function isNumber(val) {
                var regPos = /^\d+(\.\d+)?$/; //非负浮点数
                var regNeg = /^(-(([0-9]+\.[0-9]*[1-9][0-9]*)|([0-9]*[1-9][0-9]*\.[0-9]+)|([0-9]*[1-9][0-9]*)))$/; //负浮点数
                if (regPos.test(val) || regNeg.test(val)) {
                    return true;
                } else {
                    return false;
                }
            }

            for (var i = 0; i < trs.length; i++) {
                var action_id = $(trs[i]).find('.action_select option:selected').attr('data-id');
                if (action_id) {
                    var rate2 = $(trs[i]).find("input[name='rate_2']").val();
                    var rate = $(trs[i]).find("input[name='rate']").val();
                    if (!isNumber(rate)) {
                        alert('参数格式不正确');
                        return
                    }
                    if (!isInteger(rate2)) {
                        alert('次数必须为整数');
                        return
                    }

                    var res = {
                        'id': $(trs[i]).find('.action_select select').data('id'),
                        'action_id': action_id,
                        'action_name': $(trs[i]).find('.action_select option:selected').val(),
                        'rate': rate,
                        'rate_2': rate2
                    };
                    actions.push(res)

                }

            }

            var new_div = QWeb.render('action_process', {'result': actions});
            $("[dest_bom_line ="+bom_line_id+"]").find('.sel_action').html(new_div);
            // self.table_data[self.index]['process_action_1'] = $('.unlock_condition select option:selected').val();
            // if ($('.unlock_condition .change_time input').val() != '') {
            //     $('.fixed-table-body tr[data-index=' + self.index + ']').find('.adjusttime').html($('.unlock_condition .change_time input').val());
            //     self.table_data[self.index]['adjust_time'] = $('.unlock_condition .change_time input').val()
            // }
            if (self.delete_action_ids&&self.delete_action_ids[bom_line_id]) {
                actions = actions.concat(self.delete_action_ids[bom_line_id]);
            }

            self.bom_line_action_data[bom_line_id] = actions;
            console.log(self.bom_line_action_data);
            $('.unlock_condition').hide();
            if ($('.fixed-table-toolbar .save_process_sel').length == 0) {
                $('.save_process_sel').removeClass('hidden')
            }
        },

        sel_action_func: function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var self = this;
            console.log(self.bom_line_action_data);

            var dest_bom_line = parseInt($(target).parents('tr').attr('dest_bom_line'));
            console.log(dest_bom_line)
            var actions = self.bom_line_action_data[dest_bom_line];
            console.log(actions)
            console.log($('.unlock_condition'))
            $('.unlock_condition').attr('data-id', dest_bom_line).show();
            $('#action_table').html('');
            $('#action_table').append(QWeb.render('process_action_table', {
                result: actions
            }))


        },


        //更新按钮动作
        save_func: function () {
            var self = this;
            var origin_bom_id = $('.origin_bom select option:selected').attr('data-bom-id');
            self.edit_data = [];
            $('.replace select').each(function () {
                console.log($(this).find('option:selected').attr('data-id'));
                self.edit_data.push({
                    'replace_id': parseInt($(this).find('option:selected').attr('data-id')),
                    'dest_bom_line': parseInt($(this).parents('tr').attr('dest_bom_line'))
                })
            });
            console.log(self.edit_data);
            console.log(origin_bom_id);
            new Model('mrp.bom').call('save_changes', [], {
                'copy_actions': self.edit_data,
                'source_bom_id': origin_bom_id
            }).then(function (result) {
                console.log(result);
                self.confirm_target_bom_sel_func();
            })
        },
        //点击替代 获取可选择的options
        replace_func: function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var self = this;
            var origin_bom_id = $('.origin_bom select option:selected').attr('data-bom-id');
            var target_bom_id = $('.target_bom select option:selected').attr('data-bom-id');
            new Model('mrp.bom').call('get_product_options', [], {
                target_bom_id: parseInt(target_bom_id),
                origin_bom_id: parseInt(origin_bom_id)
            }).then(function (result) {
                console.log(result);
                $(target).parents('tr').find('.replace select').html('');
                $(target).parents('tr').find('.replace select').append(QWeb.render('replace_options_templ', {result: result}))
                $(target).parents('tr').find('.replace select').selectpicker('refresh')
            })
        },
        //确认目标bom的选择 渲染table表
        confirm_target_bom_sel_func: function () {
            var self = this;
            self.bom_line_action_data = {};
            var origin_bom_id = $('.origin_bom select option:selected').attr('data-bom-id');
            var target_bom_id = $('.target_bom select option:selected').attr('data-bom-id');
            new Model('mrp.bom').call('get_diff_bom_data', [], {
                target_bom_id: parseInt(target_bom_id),
                origin_bom_id: parseInt(origin_bom_id)
            }).then(function (result) {
                console.log(result);

                $.each(result, function (index, value) {
                    if (value.dest_bom_line) {
                        self.bom_line_action_data[target_bom_id] = value.dest_action_ids;
                    }

                });
                $('.cost_matching_container tbody').html('');
                $('.cost_matching_container tbody').append(QWeb.render('cost_matching_tbody_templ', {
                    result: result,
                    target: true
                }));
            })
        },
        //确认源bom的选择 渲染table表
        confirm_origin_bom_sel_func: function () {
            var bom_id = $('.origin_bom select option:selected').attr('data-bom-id');
            new Model('mrp.bom').call('get_bom_line_list', [[parseInt(bom_id)]]).then(function (result) {
                console.log(result);
                $('.cost_matching_container tbody').html('');
                $('.cost_matching_container tbody').append(QWeb.render('cost_matching_tbody_templ', {
                    result: result,
                    target: false
                }));
            })
        },
        //源bom、目标bom下的输入框搜索事件
        origin_bom_search_func: _.debounce(function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            new Model('mrp.bom').call('get_bom_list', [{name: $(target).parents('td').find('input').val()}]).then(function (result) {
                $(target).parents('td').find('select').html('');
                $.when($(target).parents('td').find('select').append(QWeb.render('cost_matching_select_templ', {result: result}))).then(function () {
                    $(target).parents('td').find('select').selectpicker('refresh')
                })
            })
        }, 300, true),

        init: function (parent, action) {
            this._super(parent);
            self.delete_action_ids={};
            this._super.apply(this, arguments);
        },
        start: function () {

        },

    });

    core.action_registry.add('bom_cost_reproduce', BomCostReproduce);

    return BomCostReproduce;


});
