/**
 * Created by allen on 2018/02/06.
 */
odoo.define('linkloving_dashboard.dashboard', function (require) {
    "use strict";

    var core = require('web.core');
    var Model = require('web.Model');
    var Widget = require('web.Widget');
    var data = require('web.data');
    var ControlPanelMixin = require('web.ControlPanelMixin');
    var pyeval = require('web.pyeval');
    var QWeb = core.qweb;
    var Dashboard = Widget.extend(ControlPanelMixin, {
        template: "Dashboard",
        events: {
            'click .sel_pro ': 'sel_pro_func',

        },


        // init: function (parent, action) {
        //     this._super(parent);
        //     this._super.apply(this, arguments);
        //     this.product_id = action.product_id;
        //     if (parent && parent.action_stack.length > 0) {
        //         this.action_manager = parent.action_stack[0].widget.action_manager
        //     }
        //
        //     if (action && action.params) {
        //         this.product_id = action.params["active_id"];
        //     }
        //     this.edit_arr = []
        // },

        start: function () {

            var self = this;
            // this.$el.css({width: this.width});
            var cp_status = {
                breadcrumbs: self.action_manager && self.action_manager.get_breadcrumbs(),
                // cp_content: _.extend({}, self.searchview_elements, {}),
            };
            self.update_control_panel(cp_status);

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
                    var self = this;
                    self.index = item.id;
                    console.log(item);
                    if (!item.bom_id) {
                        new Model('mrp.bom.line').call('parse_action_line_data', [item.id]).then(function (results) {
                            var datas = [];
                            if (results && results.length > 0) {
                                for (var i = 0; i < results.length; i++) {

                                    var res = {
                                        'line_id': results[i].line_id,
                                        'action_id': results[i].action_id,
                                        'rate': results[i].rate,
                                        'options': results[i].options,
                                        'remark': results[i].remark,
                                        'cost': results[i].cost
                                    };
                                    console.log(res);
                                    datas.push(res)
                                }
                            }
                            $('.unlock_condition').attr('data-id', item.id).show();
                            $('#action_table').html('');
                            console.log(datas);
                            $('#action_table').append(QWeb.render('process_action_table', {
                                result: datas,
                            }))

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

    core.action_registry.add('Dashboard', Dashboard);

    return CostDetail;


});
