/**
 * Created by allen on 2018/02/06.
 */
odoo.define('linkloving_account_custom_report.account_budget_report', function (require) {
    "use strict";

    var core = require('web.core');
    var Model = require('web.Model');
    var Widget = require('web.Widget');
    var data = require('web.data');
    var ControlPanelMixin = require('web.ControlPanelMixin');
    var pyeval = require('web.pyeval');
    var QWeb = core.qweb;
    var AccountCustomReport = Widget.extend(ControlPanelMixin, {
        template: "AccountCustomReport",
        events: {},
        init: function (parent, action) {
            this._super(parent);
            this._super.apply(this, arguments);
            if (parent && parent.action_stack.length > 0) {
                this.action_manager = parent.action_stack[0].widget.action_manager
            }
        },

        start: function () {

            var self = this;
            // this.$el.css({width: this.width});
            var cp_status = {
                breadcrumbs: self.action_manager && self.action_manager.get_breadcrumbs(),
                // cp_content: _.extend({}, self.searchview_elements, {}),
            };
            self.update_control_panel(cp_status);
            var colspan_xishu = 1;
            var formarter_per = function (value, row, index) {
                if (value) {
                    return toString(value * 100) + '%';
                }
                else {
                    return '';
                }
            };
            var formatter = function (value, row, index) {
                if (value) {
                    console.log(typeof value);
                    return value.formatMoney();
                }
                else {
                    return 0;
                }
            };
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
            new Model('product.product').call('search_read', [[['can_be_expensed', '=', true]]]).then(function (records) {

                _.each(records, function (result) {

                    var res = {
                        field: result['default_code'],
                        title: result['name'],
                        colspan: 1,
                        valign: "middle",
                        halign: "center",
                        align: "center",
                        formatter: formatter,


                    };
                    row5.push(res)

                });
                console.log(row5);
                var res_sub = {
                        field: 'sub_total',
                        title: '小计',
                        colspan: 1,
                        valign: "middle",
                        halign: "center",
                        align: "center",
                        formatter: formatter,

                    },
                    sale_amount = {
                        field: 'sale_target',
                        title: '预计销售额',
                        colspan: 1,
                        valign: "middle",
                        halign: "center",
                        align: "center",
                        formatter: formatter,

                    },
                    sale_expense_rate = {
                        field: 'sale_expense_rate',
                        title: '占比',
                        colspan: 1,
                        valign: "middle",
                        halign: "center",
                        align: "center",

                    }
                row5.push(res_sub);
                row5.push(sale_amount);
                row5.push(sale_expense_rate);

                var title_row = [{
                    field: 'title',
                    title: data['company_name'] + '-生产跟踪单',
                    halign: "center",
                    align: "center",
                    colspan: row5.length,
                    'class': "font_35_header",
                }]
                var row1 = [
                    {
                        field: 'total_expense_amount',
                        title: '预计总费用',
                        colspan: colspan_xishu * 2,
                        halign: "center",
                        align: "center",
                        valign: "middle", // top, middle, bottom
                    }
                ];
                var row2 = [
                    {
                        field: 'sale_amount',
                        title: '预计销售额',
                        colspan: colspan_xishu * 2,
                        halign: "center",
                        align: "center",
                        valign: "middle",
                    },
                ];

                data = [row5];


                new Model("linkloving.account.budget")
                    .call("get_department_budget_report", [], {})
                    .then(function (res) {
                        self.initTableSubCompany(res, data);
                    })
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

    core.action_registry.add('account_custom_report', AccountCustomReport);

    return AccountCustomReport;


});
