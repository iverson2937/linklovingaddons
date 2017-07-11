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
            'click .add_bom_data': 'add_bom_data_fn'
        },
        add_bom_data_fn: function () {
            var action = {
                name: "详细",
                type: 'ir.actions.act_window',
                res_model: 'add.bom.line.wizard',
                view_type: 'form',
                view_mode: 'tree,form',
                views: [[false, 'form']],
                target: "new"
            };
            this.do_action(action
            )

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
        },
        start: function () {
            var self = this;
            if (this.bom_id) {
                return new Model("mrp.bom")
                    .call("get_bom", [this.bom_id])
                    .then(function (result) {
                        console.log(result);
                        console.log(result.bom_ids);
                        var tNodes = [];

                        //获取数据存入数组
                        function get_datas(obj) {
                            for (var i = 0; i < obj.length; i++) {
                                var s = {
                                    id: obj[i].id,
                                    pId: obj[i].parent_id,
                                    name: obj[i].name,
                                    td: [obj[i].product_specs, obj[i].qty, obj[i].process_id, "<span class='fa fa-plus add_bom_data'></span>"]
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
                            name: result.name,
                            td: [result.product_specs, '', result.process_id, "<span class='fa fa-plus add_bom_data'></span>"]
                        })

                        var heads = ["名字", "规格", "数量", "工序", "添加"];
                        // var tNodes = [
                        //     { id: 1, pId: 0, name: "父节点1", td: ["parent", "1"] },
                        //     { id: 111, pId: 1, name: "叶子节点111", td: ["<a href='javascript:void(0);' onclick=\"alert('内容为html');\">parent</a>", "111"] },
                        //     { id: 11, pId: 1, name: "叶子节点112", td: ["children", "112"] },
                        //     { id: 113, pId: 111, name: "叶子节点113", td: ["children", "113"] },
                        //     { id: 114, pId: 11, name: "叶子节点114", td: ["children", "114"] },
                        //     { id: 12, pId: 1, name: "父节点12", td: ["parent", "12"] }
                        // ];
                        console.log(tNodes)
                        setTimeout(function () {
                            console.log($("#treeMenu"));
                            console.log($("#treeMenu").length);

                            $.TreeTable("treeMenu", heads, tNodes);
                        }, 200)
                    })
            }
        }
    })
    core.action_registry.add('new_bom_update', NewBomUpdate);

    return NewBomUpdate;
})