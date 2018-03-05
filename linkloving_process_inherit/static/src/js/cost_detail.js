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
            alert(this.product_id);
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
            var row5 = [{
                field: 'department_id',
                title: '部门',
                colspan: 1,
                valign: "middle",
                halign: "center",
                align: "center",
                class: 'department',
                sortable: true,

            }, {
                field: 'manpower',
                title: '预算人数',
                colspan: 1,
                valign: "middle",
                halign: "center",
                align: "center",
                sortable: true,

            }];
            new Model('product.template').call('get_product_cost_detail', [product_id]).then(function (records) {
                self.initTableSubCompany(records)

            });


        },
        initTable: function (data) {
            var self = this;
            var formatter_func = function (value, row, index) {
                if (value) {
                    if (value["sub_ip"]) {
                        var url = value["sub_ip"] + '/web?#view_type=form&model=' + value.model + '&id=' + value.id;
                    }
                    else {
                        var url = 'http://' + location.host + '/web?#view_type=form&model=' + value.model + '&id=' + value.id;
                    }
                    return '<a href="' + url + '" target="_blank">' + value.name + '</a>';
                }
                else {
                    return '';
                }
            };
            var sorter = function (a, b) {
                console.log(a);
                var aname = '';
                var bname = '';
                if (a) {
                    aname = a.name;
                }
                if (b) {
                    bname = b.name;
                }
                if (aname > bname) return 1;
                if (aname < bname) return -1;
                return 0;
            };


            var coloums = [{
                field: 'seq',
                title: '序号',
                formatter: function (value, row, index) {
                    return index + 1;
                }
            }, {
                field: 'producer',
                title: '生产者',
                sortable: true
            }, {
                field: 'so',
                title: '销售SO号',
                sortable: true,
                formatter: formatter_func,
                sorter: sorter,
            }, {
                field: 'pi_number',
                title: '销售PI号',
                sortable: true,
            }, {
                field: 'partner',
                title: '客户',
                sortable: true,
            }, {
                field: 'handle_date',
                title: '交期',
                sortable: true,
            }, {
                field: 'sale_man',
                title: '业务员',
                sortable: true,
            }, {
                field: 'follow_partner',
                title: '跟单',
                sortable: true,
            }, {
                field: 'sub_so_name',
                title: '生产SO号',
                sortable: true,
                formatter: formatter_func,
                sorter: sorter,
            }, {
                field: 'po',
                title: '采购PO号',
                sortable: true,
                formatter: formatter_func,
                sorter: sorter,
            },
                {
                    field: 'report_remark',
                    title: '备注',
                    sortable: true,
                    editable: {
                        type: 'textarea',
                        emptytext: '暂无备注',
                    }
                },
                {
                    field: 'shipping_rate',
                    title: '收货率',
                    sortable: true,
                },

            ];
            var options = self.options_init('江苏若态订单汇总' + new Date().Format("yyyy-MM-dd"), [[{
                field: 'title',
                title: '预算汇总',
                halign: "center",
                align: "center",
                colspan: coloums.length,
                'class': "font_35_header",
            }], coloums
            ], data);
            self.$('#table').bootstrapTable(options);
        },

        options_init: function (filename, coloums, datas) {
            var dict = {};
            var update_coloums = coloums[0];
            for (var i = 0; i < update_coloums.length; i++) {
                var sub_total = 0;
                for (var j = 0; j < datas.length; j++) {
                    sub_total += datas[j][update_coloums[i]['field']]
                }
                if (sub_total == 0) {
                    sub_total = ' '
                }
                dict[update_coloums[i]['field']] = parseInt(sub_total)

            }
            dict['department_id'] = '';
            dict['sale_expense_rate'] = '';
            datas.push(dict);

            return {
                cache: false,
                sortable: true,
                showToggle: true,
                search: true,
                striped: true,
                showColumns: true,
                showExport: true,

                editable: true,

                iconsPrefix: 'fa', // glyphicon of fa (font awesome)
                exportTypes: ['excel', 'png'],
                exportOptions: {
                    fileName: filename,//'生产跟踪单' + data.so_name,
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

                onEditableSave: function (field, row, oldValue, $el) {
                    console.log(row)
                    return new Model("purchase.order")
                        .call("write", [row.po.id, {report_remark: row.report_remark}])
                        .then(function (result) {

                        })
                },
            }
        },
        initTableSubCompany: function (data, colomns) {
            var self = this;
            if (!data) {
                return;
            }
            var options = self.options_init('预算汇总' + data.so_name, colomns, data);
            self.$('#table').bootstrapTable(options);
        },

    });

    core.action_registry.add('cost_detail_new', CostDetail);

    return CostDetail;


});
