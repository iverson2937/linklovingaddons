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
            'click .save_process_sel': 'save_process_sel_func'
        },
        save_process_sel_func: function () {
            var self = this;
            console.log(self.edit_arr);
            new Model('mrp.bom.line').call('save_multi_changes', [self.edit_arr], {'bom_id': self.bom_id}).then(function (results) {
                console.log(results);

                //刷新界面
                $("#table").bootstrapTable('refresh', results);
                // self.initTableSubCompany(self.columns, results)

                //    保存后要清空数组
                self.edit_arr = [];

            });
        },
        alia_cancel_func: function () {
            $('.unlock_condition').hide()
        },
        confirm_sel_func: function () {
            var self = this;
            $('.fixed-table-body tr[data-index=' + self.index + ']').find('.sel_pro').html($('.unlock_condition select option:selected').val());
            self.table_data[self.index]['process_action'] = $('.unlock_condition select option:selected').val();
            if ($('.unlock_condition .change_time input').val() != '') {
                $('.fixed-table-body tr[data-index=' + self.index + ']').find('.adjusttime').html($('.unlock_condition .change_time input').val());
                self.table_data[self.index]['adjust_time'] = $('.unlock_condition .change_time input').val()
            }
            self.edit_arr.push({
                'id': self.table_data[self.index].id,
                'process_action': $('.unlock_condition select option:selected').attr('data-id'),
                'adjust_time': self.table_data[self.index]['adjust_time'],
            });
            $('.unlock_condition').hide();
            if ($('.fixed-table-toolbar .save_process_sel').length == 0) {
                $('.fixed-table-toolbar').append("<button class='btn btn-primary save_process_sel'>保存</button>")
            }
        },
        sel_pro_func: function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var self = this;
            if ($(target).parents('tr').find('.sel_pro').html() != '-') {
                var index = $(target).parents('tr').attr('data-index');
                index = parseInt(index);
                self.index = index;
                new Model('mrp.bom.line').call('get_action_options', [self.table_data[index].id]).then(function (data) {
                    console.log(data);
                    $('.unlock_condition select').html('');
                    $('.unlock_condition select').append(QWeb.render('process_option_templ', {result: data}));
                    $('.unlock_condition').show();
                    $('.unlock_condition .change_time input').val('');
                    if (self.table_data[index].has_extra) {
                        $('.change_time').show()
                    } else {
                        $('.change_time').hide()
                    }
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
            if (action && action.context && action.context["sub_company_order_track"]) {
                this.sub_company_order_track = true;
                this.so_id = action.context["so_id"];
            }
            if (action && action.params) {
                this.so_id = action.params["active_id"];
                this.sub_company_order_track = true;
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
                        'class': 'sel_pro',
                    },
                    {
                        field: 'adjust_time',
                        title: '调整时间',
                        'class': 'adjusttime'
                    },
                    {
                        field: 'material_cost',
                        title: '材料成本',
                    }, {
                        field: 'manpower_cost',
                        title: '人工成本',
                    },
                    {
                        field: 'total_cost',
                        title: '总计',
                    }

                ];
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
                search: true,
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
                    refresh: 'glyphicon-refresh icon-refresh',
                    toggle: 'fa-lg fa-list-ul',
                    columns: 'fa-th',
                    detailOpen: 'fa fa-caret-down',
                    detailClose: 'fa fa-caret-right',
                    export: 'fa-upload',
                },
                columns: coloums,
                data: datas,//data.order_line,
                onLoadSuccess:function () {
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
            console.log(options)
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
