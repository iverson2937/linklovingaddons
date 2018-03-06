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
        events: {},
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
                var columns = [{
                    field: 'name',
                    title: '名称',
                }, {
                    field: 'product_type',
                    title: '物料类型',
                },
                    {
                        field: 'process_action',
                        title: '工序动作',
                        editable: true
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

                self.initTableSubCompany(columns, records)

            });


        },

        options_init: function (coloums, datas) {
            return {
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

                iconsPrefix: 'fa', // glyphicon of fa (font awesome)
                exportTypes: ['excel', 'png'],
                exportOptions: {
                    fileName: '成本明细',//'生产跟踪单' + data.so_name,
                    excelstyles: ['background-color', 'color', 'font-weight', 'border', 'border-top', 'border-bottom', 'border-left', 'border-right', 'font-size', 'width', 'height'],
                },
                icons: {
                    paginationSwitchDown: 'glyphicon-collapse-down icon-chevron-down',
                    paginationSwitchUp: 'glyphicon-collapse-up icon-chevron-up',
                    refresh: 'glyphicon-refresh icon-refresh',
                    toggle: 'fa-lg fa-list-ul',
                    columns: 'fa-th',
                    detailOpen: 'glyphicon-plus icon-plus',
                    detailClose: 'glyphicon-minus icon-minus',
                    export: 'fa-upload',
                },
                columns: coloums,
                data: datas,//data.order_line,
            }
        },
        initTableSubCompany: function (colomns, data) {
            var self = this;
            if (!data) {
                return;
            }


            var options = self.options_init(colomns, data);
            self.$('#table').bootstrapTable(options);
            self.$('#table').treegrid({
                    initialState: 'collapsed',//收缩
                    treeColumn: 0,//指明第几列数据改为树形
                    expanderExpandedClass: 'fa fa-caret-down',
                    expanderCollapsedClass: 'fa fa-caret-right',
                    onChange: function() {
                        self.$('#table').bootstrapTable('resetWidth');
                    }
                });
        },

    });

    core.action_registry.add('cost_detail_new', CostDetail);

    return CostDetail;


});
