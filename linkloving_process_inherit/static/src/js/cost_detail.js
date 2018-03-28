/**
 * Created by allen on 2018/02/06.
 */
odoo.define('linkloving_process_inherit.cost_detail_new', function (require) {
    "use strict";

    var core = require('web.core');
    var Model = require('web.Model');
    var Widget = require('web.Widget');
    var data = require('web.data');
    var ControlPanelMixin = require('web.ControlPanelMixin');
    var pyeval = require('web.pyeval');
    var QWeb = core.qweb;
    var CostDetail = Widget.extend(ControlPanelMixin, {
        template: "CostDetail",
        events: {
            'click .sel_action': 'sel_pro_func',
            'click .confirm_sel': 'confirm_sel_func',
            'click .alia_cancel': 'alia_cancel_func',
            'click .save_process_sel': 'save_process_sel_func',
            'click .get_default': 'get_default_func',
            'click .fa-plus-square-o': 'add_action_line_func',
            'click .fa-trash-o': 'remove_action_line_func',
            'click .custom_rate': 'custom_rate_func',

        },
        custom_rate_func: function () {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var self = this;
            var table = $(target).parents('table');
            var rates = table.find('.rate_2')
            _.each(rates, function (result) {
                $(result).removeAttr("readonly");

            });


        },
        remove_action_line_func: function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var self = this;
            var tr = $(target).parents('tr');
            if (tr.find('select').attr('data-id')) {
                self.edit_arr.push({
                    'action_line_id': tr.find('select').data('id'),
                    'delete': true
                });
            }
            tr.remove()

        },

        add_action_line_func: function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var self = this;
            var tr = $(target).parents('tr');
            var array = new Array();
            tr.find("select option").each(function () {  //遍历所有option
                var txt = $(this).data('id');   //获取option值
                if (txt != '') {
                    array.push({'id': txt, 'name': $(this).val()});  //添加到数组中
                }
            });
            console.log(array);
            var new_tr = QWeb.render('action_process_tr', {'options': array});
            $(target).parents('tr').after(new_tr);


        },

        get_default_func: function () {
            var self = this;
            new Model('product.template').call('get_product_default_cost_detail', [this.product_id]).then(function (results) {
                console.log(results);
                var show_save = false;

                //刷新界面
                $("#table").bootstrapTable('destroy');
                self.initTableSubCompany(self.columns, results);

                _.each(results, function (result) {
                    if (result.is_default) {
                        show_save = true;
                        console.log(result);
                        self.edit_arr.push({
                            'id': result.id,
                            'actions': result.process_action
                        });
                    }
                });
                if (show_save) {
                    $('.save_process_sel').removeClass('hidden')
                }

            });

        },

        save_process_sel_func: function () {
            var self = this;
            console.log(self.edit_arr);
            new Model('mrp.bom.line').call('save_multi_changes', [self.edit_arr], {'bom_id': self.bom_id}).then(function (results) {
                console.log(self.edit_arr);

                //刷新界面
                $("#table").bootstrapTable('destroy');
                self.initTableSubCompany(self.columns, results);

                //    保存后要清空数组
                self.edit_arr = [];

            });
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
                return Math.floor(obj) === obj
            }

            for (var i = 0; i < trs.length; i++) {
                var action_id = $(trs[i]).find('select option:selected').attr('data-id');
                if (action_id) {
                    var rate2 = $(trs[i]).find("input[name='rate_2']").val();
                    if (!isInteger(rate2)) {
                        alert('自定义比例必须为整数')
                    }
                    var res = {
                        'id': $(trs[i]).find('select').data('id'),
                        'action_id': action_id,
                        'action_name': $(trs[i]).find('select option:selected').val(),
                        'rate': $(trs[i]).find("input[name='rate']").val(),
                        'rate_2': rate2
                    };
                    actions.push(res)

                }

            }

            var new_div = QWeb.render('action_process', {'result': actions});
            $('.treegrid-' + bom_line_id).find('.sel_action').html(new_div);
            // self.table_data[self.index]['process_action_1'] = $('.unlock_condition select option:selected').val();
            // if ($('.unlock_condition .change_time input').val() != '') {
            //     $('.fixed-table-body tr[data-index=' + self.index + ']').find('.adjusttime').html($('.unlock_condition .change_time input').val());
            //     self.table_data[self.index]['adjust_time'] = $('.unlock_condition .change_time input').val()
            // }
            console.log(self.table_data);
            console.log(self.index);
            console.log(self);
            self.edit_arr.push({
                'id': parseInt(bom_line_id),
                'actions': actions
            });
            console.log(self.edit_arr);
            $('.unlock_condition').hide();
            if ($('.fixed-table-toolbar .save_process_sel').length == 0) {
                $('.save_process_sel').removeClass('hidden')
            }
        },
        sel_pro_func: function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var self = this;
            var index = $(target).parents('tr').attr('data-index');
            index = parseInt(index);
            self.index = index;
            console.log(self.table_data)

            if (!self.table_data.bom_id) {
                new Model('mrp.bom.line').call('parse_action_line_data', [self.table_data[index].id]).then(function (results) {
                    var datas = [];
                    if (results && results.length > 0) {
                        for (var i = 0; i < results.length; i++) {

                            var res = {
                                'line_id': results[i].line_id,
                                'action_id': results[i].action_id,
                                'rate': results[i].rate,
                                'options': results[i].options,
                                'remark': results[i].remark,
                                'cost': results[i].cost,
                                'rate_2': results[i].rate_2
                            };
                            datas.push(res)
                        }
                    }
                    $('.unlock_condition').attr('data-id', self.table_data[index].id).show();
                    $('#action_table').html('');
                    console.log(datas);
                    $('#action_table').append(QWeb.render('process_action_table', {
                        result: datas
                    }))


                })

            }
        },

        init: function (parent, action) {
            this._super(parent);
            this._super.apply(this, arguments);
            this.product_id = action.product_id;
            if (parent && parent.action_stack.length > 0) {
                this.action_manager = parent.action_stack[0].widget.action_manager
            }

            if (action && action.params) {
                this.product_id = action.params["active_id"];
            }
            this.edit_arr = []
        },

        start: function () {

            var self = this;
            var product_id = self.product_id;
            // this.$el.css({width: this.width});
            var cp_status = {
                breadcrumbs: self.action_manager && self.action_manager.get_breadcrumbs(),
                // cp_content: _.extend({}, self.searchview_elements, {}),
            };
            self.update_control_panel(cp_status);

            var formatter_func = function (value, row, index) {


                var res = QWeb.render('action_process', {'result': value});
                return res
            };
            new Model('product.template').call('get_product_cost_detail', [product_id]).then(function (records) {
                console.log(records);
                self.table_data = records;
                self.bom_id = records[0].bom_id;
                var columns = [{
                        field: 'name',
                        title: '名称',
                    }, {
                        field: 'product_type',
                        title: '物料类型',
                    },
                        {
                            field: 'qty',
                            title: '配比',
                        },
                        {
                            field: 'process_action',
                            title: '工序动作',
                            class: 'sel_action',
                            formatter: formatter_func

                        },

                        {
                            field: 'material_cost',
                            title: '材料成本',
                        }
                        ,
                        {
                            field: 'manpower_cost',
                            title: '人工成本',
                        }
                        ,
                        {
                            field: 'total_cost',
                            title: '总计',
                        }

                    ]
                ;
                self.columns = columns;
                self.initTableSubCompany(columns, records)

            });


        },

        options_init: function (coloums, datas) {
            return {
                contentType: 'application/json',
                method: 'post',
                cache: false,
                sortable: true,
                showToggle: true,
                // search: true,
                striped: true,
                stickyHeader: true,
                showColumns: true,
                showExport: true,
                treeShowField: 'name',
                treeEnable: true,
                idField: 'id',
                parentIdField: 'pid',
                editable: true,
                showRefresh: true,
                iconsPrefix: 'fa', // glyphicon of fa (font awesome)
                exportTypes: ['excel', 'png'],
                exportOptions: {
                    fileName: '成本明细',//'生产跟踪单' + data.so_name,
                    excelstyles: ['background-color', 'color', 'font-weight', 'border', 'border-top', 'border-bottom', 'border-left', 'border-right', 'font-size', 'width', 'height'],
                },
                icons: {
                    paginationSwitchDown: 'fa fa-caret-down',
                    paginationSwitchUp: 'fa fa-caret-right',
                    refresh: 'fa fa-refresh',
                    toggle: 'fa-lg fa-list-ul',
                    columns: 'fa-th',
                    detailOpen: 'fa fa-caret-down',
                    detailClose: 'fa fa-caret-right',
                    export: 'fa-upload',
                },
                columns: coloums,
                data: datas,//data.order_line,
                onLoadSuccess: function () {
                    self.$('#table').treegrid({
                        // initialState: 'collapsed',//收缩
                        treeColumn: 0,//指明第几列数据改为树形
                        expanderExpandedClass: 'fa fa-caret-down',
                        expanderCollapsedClass: 'fa fa-caret-right',
                        onChange: function () {
                            self.$('#table').bootstrapTable('resetWidth');
                        }
                    });
                },

                onClickRow: function (item, $element) {


                },

                onEditableSave: function (field, row, oldValue, $el) {
                    console.log(row)
                },
            }
        },
        initTableSubCompany: function (colomns, data) {
            var self = this;
            if (!data) {
                return;
            }
            var options = self.options_init(colomns, data);
            // options = $.extend(options, {
            //     url: '/linkloving_process_inherit/get_bom_cost',
            //     queryParams: {'bom_id': data[0].bom_id},
            // });
            self.options = options;
            self.$('#table').bootstrapTable(options);
            self.$('#table').treegrid({
                // initialState: 'collapsed',//收缩
                treeColumn: 0,//指明第几列数据改为树形
                expanderExpandedClass: 'fa fa-caret-down',
                expanderCollapsedClass: 'fa fa-caret-right',
                onChange: function () {
                    self.$('#table').bootstrapTable('resetWidth');
                }
            });
        },

    });

    core.action_registry.add('cost_detail_new', CostDetail);

    return CostDetail;


});
