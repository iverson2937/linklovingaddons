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
            'click .sel_pro ': 'sel_pro_func',
            'click .confirm_sel': 'confirm_sel_func',
            'click .alia_cancel': 'alia_cancel_func',
            'click .adjusttime': 'sel_pro_func',
            'click .save_process_sel': 'save_process_sel_func',
            'click .get_default': 'get_default_func',
            'click .fa-plus-square-o': 'add_action_line_func',

        },
        add_action_line_func: function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var self = this;
            $(target).parents('tr').append(" <b>Hello world!</b>");


        },

        get_default_func: function () {
            var self = this;
            new Model('mrp.bom.line').call('get_default_data', [self.edit_arr], {'bom_id': self.bom_id}).then(function (results) {
                console.log(results);

                //刷新界面
                $("#table").bootstrapTable('destroy');

                //    保存后要清空数组
                self.edit_arr = [];

            });

        },
        save_process_sel_func: function () {
            var self = this;
            console.log(self.edit_arr);
            new Model('mrp.bom.line').call('save_multi_changes', [self.edit_arr], {'bom_id': self.bom_id}).then(function (results) {
                console.log(results);

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
            var bom_line_id = $('.unlock_condition').data('id');
            var action_1 = $('.sel_action_1 select option:selected').val();
            var action_2 = $('.sel_action_2 select option:selected').val();
            var result = [];


            $('.treegrid-' + bom_line_id).find('.sel_action').html(action_2);
            // self.table_data[self.index]['process_action_1'] = $('.unlock_condition select option:selected').val();
            // if ($('.unlock_condition .change_time input').val() != '') {
            //     $('.fixed-table-body tr[data-index=' + self.index + ']').find('.adjusttime').html($('.unlock_condition .change_time input').val());
            //     self.table_data[self.index]['adjust_time'] = $('.unlock_condition .change_time input').val()
            // }
            console.log(self.table_data);
            console.log(self.index);
            console.log(self);
            self.edit_arr.push({
                'id': self.table_data[self.index].id,
                'process_action_1': action_1,
                'process_action_2': action_2,
            });
            $('.unlock_condition').hide();
            if ($('.fixed-table-toolbar .save_process_sel').length == 0) {
                $('.fixed-table-toolbar').append("<button class='btn btn-primary save_process_sel'>保存</button>")
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


                var abc = QWeb.render('action_process');
                // QWeb.render('action_process')
                //  var res = '<div>';
                //  if (value) {
                //      for (var i = 0; i < value.length; i++) {
                //          res = res + value[i]['action_name'] + '<span>' + res + value[i]['rate'] + '</span>'
                //      }
                //  }
                //  res + '</div>'


                return abc
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
                            title:
                                '材料成本',
                        }
                        ,
                        {
                            field: 'manpower_cost',
                            title:
                                '人工成本',
                        }
                        ,
                        {
                            field: 'total_cost',
                            title:
                                '总计',
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
                    var self = this;
                    self.index = item.id;
                    console.log(this);
                    if (!item.bom_id) {
                        console.log(item)
                        console.log($element)

                        new Model('mrp.bom.line').call('parse_action_line_data', [item.id]).then(function (data) {
                            var data = [
                                {'line_id': 1, 'selected_action_id': 1, 'selected_action_name': '包装', 'rate': 1},
                                {'action_id': 2, 'action_name': '包装', 'rate': 1}
                            ];
                            var options = [
                                {
                                    'id': 1,
                                    'name': '包装'
                                },
                                {
                                    'id': 2,
                                    'name': '包装1'
                                }
                            ]
                            $('.unlock_condition').show();
                            $('#action_table').html();
                            $('#action_table').append(QWeb.render('process_action_table', {
                                result: data,
                                options: options
                            }));
                            // $('.unlock_condition').attr('data-id', item.id).show();
                            // if (self.table_data[index].has_extra) {
                            //     $('.change_time').show()
                            // } else {
                            //     $('.change_time').hide()
                            // }

                        })

                    }

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
            options = $.extend(options, {
                url: '/linkloving_process_inherit/get_bom_cost',
                queryParams: {'bom_id': data[0].bom_id},
            });
            self.options = options;
            self.$('#table').bootstrapTable(options);
            self.$('#table').treegrid({
                initialState: 'collapsed',//收缩
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
