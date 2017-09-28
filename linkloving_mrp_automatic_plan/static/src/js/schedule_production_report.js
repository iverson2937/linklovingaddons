/**
 * Created by 123 on 2017/8/31.
 */
odoo.define('linkloving_mrp_automatic_plan.schedule_production_report', function (require) {
    "use strict";
    var core = require('web.core');
    var Model = require('web.Model');
    var data_manager = require('web.data_manager');
    var ControlPanelMixin = require('web.ControlPanelMixin');
    var ControlPanel = require('web.ControlPanel');
    var Widget = require('web.Widget');
    var data = require('web.data');
    var ListView = require('web.ListView');
    var common = require('web.form_common');
    var Pager = require('web.Pager');
    var datepicker = require('web.datepicker');
    var Dialog = require('web.Dialog');
    var framework = require('web.framework');
    var SearchView = require('web.SearchView');
    var pyeval = require('web.pyeval');
    var QWeb = core.qweb;
    var _t = core._t;
    var myself;

    var Schedule_Production_Report = Widget.extend(ControlPanelMixin, {
        template: 'schedule_production_tmpl',
        events: {},
        init: function (parent, action) {
            this._super(parent);
            this._super.apply(this, arguments);
            console.log("13123")
            if (parent && parent.action_stack.length > 0) {
                this.action_manager = parent.action_stack[0].widget.action_manager
            }

            var self = this;
        },
        start: function () {
            var self = this;
            var cp_status = {
                breadcrumbs: self.action_manager && self.action_manager.get_breadcrumbs(),
                // cp_content: _.extend({}, self.searchview_elements, {}),
            };
            self.update_control_panel(cp_status);

            setTimeout(function () {
                self.initTreeTable()

            }, 1000);
        },
        initTreeTable: function () {
            var jsonData = {
                "nodeID": {
                    "1": [

                        {
                            "ID": "1.1",
                            "childNodeType": "branch",
                            "childData": [
                                "1.1: column 1",
                                "1.1: column 2"
                            ]
                        },
                        {
                            "ID": "1.2",
                            "childNodeType": "leaf",
                            "childData": [
                                "1.2: column 1",
                                "1.2: column 2"
                            ]
                        },
                        {
                            "ID": "1.3",
                            "childNodeType": "leaf",
                            "childData": [
                                "1.3: column 1",
                                "1.3: column 2"
                            ]
                        }

                    ],
                    "1.1": [

                        {
                            "ID": "1.1.1",
                            "childNodeType": "branch",
                            "childData": [
                                "1.1.1: column 1",
                                "1.1.1: column 2"
                            ]
                        },
                        {
                            "ID": "1.1.2",
                            "childNodeType": "leaf",
                            "childData": [
                                "1.1.2: column 1",
                                "1.1.2: column 2"
                            ]
        }

                    ],
                    "2": [

                        {
                            "ID": "2.1",
                            "childNodeType": "leaf",
                            "childData": [
                                "2.1: column 1",
                                "2.1: column 2"
                            ]
                        },
                        {
                            "ID": "2.2",
                            "childNodeType": "leaf",
                            "childData": [
                                "2.2: column 1",
                                "2.2: column 2"
                            ]
                        },
                        {
                            "ID": "2.3",
                            "childNodeType": "leaf",
                            "childData": [
                                "2.3: column 1",
                                "2.3: column 2"
                            ]
                        }

                    ],
                    "3": [

                        {
                            "ID": "3.1",
                            "childNodeType": "leaf",
                            "childData": [
                                "3.1: column 1",
                                "3.1: column 2"
                            ]
                        },
                        {
                            "ID": "3.2",
                            "childNodeType": "leaf",
                            "childData": [
                                "3.2: column 1",
                                "3.2: column 2"
                            ]
                        },
                        {
                            "ID": "3.3",
                            "childNodeType": "leaf",
                            "childData": [
                                "3.3: column 1",
                                "3.3: column 2"
                            ]
                        }

                    ],
                    "1.1.1": [

                        {
                            "ID": "1.1.1.1",
                            "childNodeType": "leaf",
                            "childData": [
                                "1.1.1: column 1",
                                "1.1.1: column 2"
                            ]
                        },
                        {
                            "ID": "1.1.2",
                            "childNodeType": "leaf",
                            "childData": [
                                "1.1.2: column 1",
                                "1.1.2: column 2"
                            ]
                        }

                    ]
                }
            };
            // initialize treeTable
            $("#example-basic").treetable({
                expandable: true,
                onNodeExpand: nodeExpand,
                onNodeCollapse: nodeCollapse
            });
            $("#example-basic").treetable("reveal", '1');
            $("#example-basic tbody").on("mousedown", "tr", function () {
                $(".selected").not(this).removeClass("selected");
                $(this).toggleClass("selected");
            });
            function nodeExpand() {
                // alert("Expanded: " + this.id);
                getNodeViaAjax(this.id);
            }


            function nodeCollapse() {
                // alert("Collapsed: " + this.id);
            }

            function getNodeViaAjax(parentNodeID) {
                $("#loadingImage").show();

                // ajax should be modified to only get childNode data from selected nodeID
                // was created this way to work in jsFiddle
                //        $.ajax({
                //            type: 'POST',
                //            url: '/echo/json/',
                //            data: {
                //                json: JSON.stringify( jsonData )
                //            },
                //            success: function(data) {
                var data = jsonData;
                $("#loadingImage").hide();

                var childNodes = data.nodeID[parentNodeID];

                if (childNodes) {
                    var parentNode = $("#example-basic").treetable("node", parentNodeID);

                    for (var i = 0; i < childNodes.length; i++) {
                        var node = childNodes[i];

                        var nodeToAdd = $("#example-basic").treetable("node", node['ID']);

                        // check if node already exists. If not add row to parent node
                        if (!nodeToAdd) {
                            // create row to add
                            var row = '<tr data-tt-id="' +
                                node['ID'] +
                                '" data-tt-parent-id="' +
                                parentNodeID + '" ';
                            if (node['childNodeType'] == 'branch') {
                                row += ' data-tt-branch="true" ';
                            }

                            row += ' >';

                            // Add columns to row
                            for (var index in node['childData']) {
                                var data = node['childData'][index];
                                row += "<td>" + data + "</td>";
                            }

                            // End row
                            row += "</tr>";

                            $("#example-basic").treetable("loadBranch", parentNode, row);
                        }


                    }

                }

                //    },
                //    error:function(error){
                //        $("#loadingImage").hide();
                //        alert('there was an error');
                //    },
                //    dataType: 'json'
                //});
            }


        }


    });

    core.action_registry.add('schedule_production_report', Schedule_Production_Report);

    return Schedule_Production_Report;
});



