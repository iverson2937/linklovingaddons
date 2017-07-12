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
          'click .add_bom_data':'add_bom_data_fn',
          'click .product_name':'product_name_fn',
          'click .new_bom_modify_submit':'new_bom_modify_submit_fn',
          'click .new_bom_modify_direct':'new_bom_modify_submit_fn'
        },
        //提交的动作
        new_bom_modify_submit_fn:function (e) {
            var e = e||window.event;
            var target = e.target||e.srcElement;


        },
        //点击产品名弹出相应的产品页面
        product_name_fn:function (e) {
            var e = e||window.event;
            var target = e.target||e.srcElement;
            var action = {
                name:"产品",
                type: 'ir.actions.act_window',
                res_model:'product.template',
                view_type: 'form',
                view_mode: 'tree,form',
                views: [[false, 'form']],
                res_id: parseInt($(target).attr("data-pt-id")),
                target:"new"
            };
            this.do_action(action);
        },
        //添加按钮的点击事件
        add_bom_data_fn: function (e) {
            var e = e||window.event;
            var target = e.target||e.srcElement;
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
            self.$(document).ajaxComplete(function (event, xhr, settings) {
                // "{"jsonrpc":"2.0","method":"call","params":{"model":"review.process.wizard","method":"search_read","args":[[["id","in",[10]]],["remark","partner_id","display_name","__last_update"]],"kwargs":{"context":{"lang":"zh_CN","tz":"Asia/Shanghai","uid":1,"default_product_attachment_info_id":"4","params":{},"bin_size":true,"active_test":false}}},"id":980816587}"
                // console.log(settings)
                var data = JSON.parse(settings.data);
                if (data.params.model == 'add.bom.line.wizard') {
                    if (data.params.method == 'action_post' && my.flag==true) {
                        my .flag = false;
                        console.log(xhr);
                        //table树重新渲染
                        var s = {
                            id: 100,
                            pId: pId,
                            ptid:xhr.responseJSON.result.product_tmpl_id,
                            name:xhr.responseJSON.result.name[0][1],
                            td:[xhr.responseJSON.result.product_spec,xhr.responseJSON.result.qty, xhr.responseJSON.result.process_id, "<span class='fa fa-plus add_bom_data'></span>"]
                        };
                        my.xNodes.push(s);
                        $("#treeMenu").html("");
                        var heads = ["名字", "规格", "数量", "工序", "添加"];
                        $.TreeTable("treeMenu", heads, my.xNodes);

                        // var c = {
                        //     modify_type : "add",
                        //     qty: xhr.responseJSON.result.qty,
                        //     product_id : xhr.responseJSON.result.name[0][0],
                        //     input_changed_value: xhr.responseJSON.result.name[0][1],
                        //     parents: ""
                        // }

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
            self.changes_back = [];
            $(".o_content").css("background","white")
        },
        // getParents: function($obj) {
        //     if ($obj.parents(".panel-collapse")) {
        //         if ($obj.parents(".panel-collapse").length == 0) {
        //             return;
        //         }
        //         arr.push($obj.parents(".panel-collapse").attr("data-return-id"));
        //         $obj = $obj.parents(".panel-collapse");
        //         getParents($obj);
        //     }
        // },
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
                                    ptid: obj[i].product_tmpl_id,
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
                            ptid: result.product_tmpl_id,
                            name: result.name,
                            td: [result.product_specs, '', result.process_id, "<span class='fa fa-plus add_bom_data'></span>"]
                        })
                        self.xNodes = tNodes;
                        var heads = ["名字", "规格", "数量", "工序", "添加"];
                        setTimeout(function () {
                            $("#treeMenu").attr("data-bom-id",result.bom_id)
                            $.TreeTable("treeMenu", heads, tNodes);
                        }, 200)
                    })
            }
        }
    })
    core.action_registry.add('new_bom_update', NewBomUpdate);

    return NewBomUpdate;
})