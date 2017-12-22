/**
 * Created by allen on 2017/11/22.
 */
odoo.define('linkloving_companies_ordercreated.sub_company_report', function (require) {
    "use strict";

    var core = require('web.core');
    var Model = require('web.Model');
    var Widget = require('web.Widget');
    var data = require('web.data');
    var ListView = require('web.ListView');
    var common = require('web.form_common');
    var Pager = require('web.Pager');
    var pyeval = require('web.pyeval');
    var QWeb = core.qweb;
    var datepicker = require('web.datepicker');
    var SubCompanyReport = Widget.extend({
        template: "SubCompanyReport",
        events: {},
        init: function (parent, action) {
            this._super(parent);
            this._super.apply(this, arguments);
            if (parent && parent.action_stack.length > 0) {
                this.action_manager = parent.action_stack[0].widget.action_manager
            }
            var self = this;
        },

        start: function () {
            var self = this;
            new Model("sub.company.report")
                .call("get_report")
                .then(function (res) {
                    var data = res;
                    self.initTable(data);
                })
        },
        initTable: function (data) {
            var coloums = [{
                field: 'seq',
                title: '序号',
                formatter: function (value, row, index) {
                    return index + 1;
                }
            }, {
                field: 'producer',
                title: '生产者',
                sortable: true,
            }, {
                field: 'so_name',
                title: '销售SO号',
                sortable: true,
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
            }, {
                field: 'po_name',
                title: '采购PO号',
                sortable: true,
            }, {
                field: 'state',
                title: '出货状态',
                sortable: true,
            }]
            self.$('#table').bootstrapTable({
                cache: false,
                sortable: true,
                showToggle: true,
                search: true,
                striped: true,
                showColumns: true,
                showExport: true,
                iconsPrefix: 'fa', // glyphicon of fa (font awesome)
                exportTypes: ['csv', 'txt', 'excel'],
                exportOptions: {
                    fileName: '江苏若态订单汇总' + new Date().Format("yyyy-MM-dd"),
                    excelstyles: ['border-bottom', 'border-top', 'border-left', 'border-right'],
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
                columns: [[{
                    field: 'title',
                    title: '江苏若态订单汇总',
                    halign: "center",
                    align: "center",
                    colspan: coloums.length,
                    'class': "font_35_header",
                }], coloums
                ],
                data: data
            });
        }
    });

    core.action_registry.add('sub_company_report', SubCompanyReport);

    return SubCompanyReport;


});
