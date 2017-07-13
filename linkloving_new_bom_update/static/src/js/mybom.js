/**
 * Created by 123 on 2017/7/10.
 */
odoo.define('linkloving_new_bom_update.new_bom_update', function (require) {
    "use strict";

    var core = require('web.core');
    var Model = require('web.Model');
    var Widget = require('web.Widget');

    var QWeb = core.qweb;
    var _t = core._t;


    var NewBomUpdate = Widget.extend({
        template: 'my_bom_container',
        events: {
            'click .add_bom_data': 'add_bom_data_fn',
            'click .product_name': 'product_name_fn',
            'click .new_bom_modify_submit': 'new_bom_modify_submit_fn',
            'click .new_bom_modify_direct': 'new_bom_modify_submit_fn'
        },

        //提交的动作
        new_bom_modify_submit_fn: function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;


        },
        //点击产品名弹出相应的产品页面
        product_name_fn: function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var action = {
                name: "产品",
                type: 'ir.actions.act_window',
                res_model: 'product.template',
                view_type: 'form',
                view_mode: 'tree,form',
                views: [[false, 'form']],
                res_id: parseInt($(target).attr("data-pt-id")),
                target: "new"
            };
            this.do_action(action);
        },
        edit_bom_line_fn: function (e) {
            var action = {
                name: "详细",
                type: 'ir.actions.act_window',
                res_model: 'add.bom.line.wizard',
                view_type: 'form',
                view_mode: 'tree,form',
                views: [[false, 'form']],
                context: {
                    'default_product_id': this.view.dataset.model,
                },
                target: "new"
            };


        },
        //添加按钮的点击事件
        add_bom_data_fn: function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var pId = $(target).parents("tr").attr("data-tt-id");
            var my = this;
            my.flag = true;
            var action = {
                name: "详细",
                type: 'ir.actions.act_window',
                res_model: 'add.bom.line.wizard',
                view_type: 'form',
                view_mode: 'tree,form',
                views: [[false, 'form']],
                target: "new"
            };
            this.do_action(action);

            //清空之前的数组，再执行查找父级id的函数
            my.parentsid = [];
            my.getParents($(target).parents("tr"));

            self.$(document).ajaxComplete(function (event, xhr, settings) {
                var data = JSON.parse(settings.data);
                if (data.params.model == 'add.bom.line.wizard') {
                    if (data.params.method == 'action_post' && my.flag == true) {
                        my.flag = false;
                        console.log(xhr);
                        //table树重新渲染
                        var s = {
                            id: 100,
                            pId: pId,
                            add: 1,
                            ptid: xhr.responseJSON.result.product_tmpl_id,
                            name: xhr.responseJSON.result.name[0][1],
                            td: [xhr.responseJSON.result.product_spec, xhr.responseJSON.result.qty, xhr.responseJSON.result.process_id,
                                "<span class='fa fa-plus-square-o add_bom_data'></span>", "<span class='fa fa-edit new_product_edit'></span>"]
                        };
                        my.xNodes.push(s);
                        $("#treeMenu").html("");
                        var heads = ["名字", "规格", "数量", "工序", "添加", "编辑"];
                        $.TreeTable("treeMenu", heads, my.xNodes);
                        $("#treeMenu").treetable("node", $("#treeMenu").attr("data-bom-id")).toggle();

                        var c = {
                            modify_type: "add",
                            qty: xhr.responseJSON.result.qty,
                            product_id: xhr.responseJSON.result.name[0][0],
                            input_changed_value: xhr.responseJSON.result.new_name,
                            parents: my.parentsid
                        }
                        my.changes_back.push(c);
                        console.log(my.changes_back);
                    }
                }
            })

        },
        init: function (parent, action) {
            this._super.apply(this, arguments);
            this.bom_id = action.bom_id;
            if (action.bom_id) {
                this.bom_id = action.bom_id;
            } else {
                this.bom_id = action.params.active_id;
            }
            var self = this;
            self.xNodes = [];
            self.flag = true;
            //返回给后台的数组
            self.changes_back = [];
            //存储父级id的数组
            self.parentsid = [];
            $(".o_content").css("background", "white")
        },

        //查找父级的递归函数
        getParents: function ($obj) {
            var self = this;
            self.parentsid.push($obj.attr("data-tt-id"));
            if ($obj.attr("data-tt-parent-id")) {
                var p = $obj.attr("data-tt-parent-id");
                $obj = $obj.prevAll("tr[data-tt-id=" + p + "]");
                self.getParents($obj);
            } else {
                return;
            }
        },

        start: function () {
            var self = this;
            if (this.bom_id) {
                return new Model("mrp.bom")
                    .call("get_bom", [this.bom_id])
                    .then(function (result) {
                        console.log(result);
                        var tNodes = [];

                        //获取数据存入数组

                        function get_datas(obj) {
                            for (var i = 0; i < obj.length; i++) {
                                var s = {
                                    id: obj[i].id,
                                    pId: obj[i].parent_id,
                                    ptid: obj[i].product_tmpl_id,
                                    name: obj[i].name,
                                    td: [obj[i].product_specs, obj[i].qty, obj[i].process_id, "<span class='fa fa-plus-square-o add_bom_data'></span>", "<span class='fa fa-edit new_product_edit'></span>"]
                                };
                                tNodes.push(s);
                                if (obj[i].bom_ids.length > 0) {
                                    get_datas(obj[i].bom_ids);
                                }
                            }
                        }

                        get_datas(result.bom_ids);
                        console.log(tNodes);
                        tNodes.push({
                            id: result.bom_id,
                            pId: 0,
                            ptid: result.product_tmpl_id,
                            name: result.name,
                            td: [result.product_specs, '', result.process_id, "<span class='fa fa-plus-square-o add_bom_data'></span>", "<span class='fa fa-edit new_product_edit'></span>"]
                        })
                        self.xNodes = tNodes;
                        var heads = ["名字", "规格", "数量", "工序", "添加", "编辑"];
                        setTimeout(function () {
                            $("#treeMenu").attr("data-bom-id", result.bom_id)
                            $.TreeTable("treeMenu", heads, tNodes);
                            $("#treeMenu").treetable("node", result.bom_id).toggle();
                        }, 200)
                    })
            }
        }
    })
    core.action_registry.add('new_bom_update', NewBomUpdate);

    return NewBomUpdate;
})