/**
 * Created by 123 on 2017/7/10.
 */
odoo.define('linkloving_new_bom_update.new_bom_update', function (require) {
    "use strict";

    var core = require('web.core');
    var Model = require('web.Model');
    var Widget = require('web.Widget');
    var View = require('web.View');
    var Dialog = require('web.Dialog');

    var QWeb = core.qweb;
    var _t = core._t;


    var NewBomUpdate = Widget.extend({
        template: 'my_bom_container',
        events: {
            'click .add_bom_data': 'add_bom_data_fn',
            'click .product_name': 'product_name_fn',
            'click .new_bom_modify_submit': 'new_bom_modify_submit_fn',
            'click .new_bom_modify_direct': 'new_bom_modify_submit_fn',
            'click .new_product_edit': 'edit_bom_line_fn',
            'click .new_product_delete': 'delete_bom_line_fn'
        },

        //删除的动作
        delete_bom_line_fn:function(e){
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var del_id = $(target).parents("tr").attr("data-tt-id");
            var self = this;

            self.parentsid = [];
            self.getParents($(target).parents("tr"));
            var message = ("确定删除这条记录？");
            var def = $.Deferred();
            var options = {
                title: _t("Warning"),
                //确认删除的操作
                confirm_callback: function() {
                    console.log('yes');
                    console.log(del_id);
                    self.xNodes.forEach(function (v, i) {
                        if(self.xNodes[i].id == del_id){
                            console.log(self.xNodes[i]);
                            self.xNodes.splice(i,1);
                            $("#treeMenu").html("");
                            var heads = ["名字", "规格", "数量", "工序", "添加", "编辑","删除"];
                            $.TreeTable("treeMenu", heads, self.xNodes);
                            $("#treeMenu").treetable("node", $("#treeMenu").attr("data-bom-id")).toggle();

                            //返回给后台的数据
                            var c = {
                                    modify_type: "delete",
                                    parents: self.parentsid
                              }
                              self.changes_back.push(c);
                              console.log(self.changes_back);
                            return;
                        }
                    })


                    self.$el.removeClass('oe_form_dirty');
                    this.on('closed', null, function() { // 'this' is the dialog widget
                        def.resolve();
                    });
                },
                cancel_callback: function() {
                    console.log('no')
                    def.reject();
                },
            };
            var dialog = Dialog.confirm(this, message, options);
            dialog.$modal.on('hidden.bs.modal', function() {
                def.reject();
            });

            return def;
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
        //编辑按钮的点击事件
        edit_bom_line_fn: function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var product_id = $(target).parents("tr").attr("data-product-id");
            var pId = $(target).parents("tr").attr("data-tt-id");
            var action = {
                name: "详细",
                type: 'ir.actions.act_window',
                res_model: 'add.bom.line.wizard',
                view_type: 'form',
                view_mode: 'tree,form',
                views: [[false, 'form']],
                context: {
                    'default_product_id': parseInt(product_id),
                    'pid':pId
                },
                target: "new"
            };
            this.do_action(action);
            var my = this;
            my.flag = true;
            my.parentsid = [];
            my.getParents($(target).parents("tr"));

            self.$(document).ajaxComplete(function (event, xhr, settings) {
               var data = JSON.parse(settings.data);
               if (data.params.model == 'add.bom.line.wizard') {
                   if (data.params.method == 'action_edit' && my.flag == true) {
                       my.flag = false;
                       console.log(xhr.responseJSON.result);
                       for(var i=0;i<my.xNodes.length;i++){
                          if(my.xNodes[i].id == xhr.responseJSON.result.pid){
                              console.log(my.xNodes[i]);

                              //table树重新渲染
                              if(xhr.responseJSON.result.new_name!=false){
                                  my.xNodes[i].name = xhr.responseJSON.result.new_name;
                              }else {
                                   my.xNodes[i].name = xhr.responseJSON.result.name[0][1];
                              }
                              my.xNodes[i].id = xhr.responseJSON.result.id;
                              my.xNodes[i].add = 2;
                              my.xNodes[i].td = [xhr.responseJSON.result.product_spec,xhr.responseJSON.result.qty, xhr.responseJSON.result.process_id,
                                        "<span class='fa fa-plus-square-o add_bom_data'></span>", "<span class='fa fa-edit new_product_edit'></span>",
                              "<span class='fa fa-trash-o new_product_delete'></span>"]
                              console.log(my.xNodes);
                              $("#treeMenu").html("");
                              var heads = ["名字", "规格", "数量", "工序", "添加", "编辑","删除"];
                              $.TreeTable("treeMenu", heads, my.xNodes);
                              $("#treeMenu").treetable("node", $("#treeMenu").attr("data-bom-id")).toggle();

                              //传给后台的数据
                              var c = {
                                    modify_type: "edit",
                                    qty: xhr.responseJSON.result.qty,
                                    product_id: xhr.responseJSON.result.name[0][0],
                                    input_changed_value: xhr.responseJSON.result.new_name,
                                    parents: my.parentsid,
                                    product_spec:xhr.responseJSON.result.product_spec
                              }
                              my.changes_back.push(c);
                              console.log(my.changes_back);
                              break;
                          }
                       }
                   }
               }
            })

        },
        //添加按钮的点击事件
        add_bom_data_fn: function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var pId = $(target).parents("tr").attr("data-tt-id");
            console.log(pId);
            var my = this;
            my.flag = true;
            var action = {
                name: "详细",
                type: 'ir.actions.act_window',
                res_model: 'add.bom.line.wizard',
                view_type: 'form',
                view_mode: 'tree,form',
                context:{'pid':pId},
                views: [[false, 'form']],
                target: "new"
            };
            this.do_action(action);

            //清空之前的数组，再执行查找父级id的函数
            my.parentsid = [];
            my.getParents($(target).parents("tr"));

            self.$(document).ajaxComplete(function (event, xhr, settings) {
                var data = JSON.parse(settings.data);
                // console.log(settings);
                if (data.params.model == 'add.bom.line.wizard') {
                    if (data.params.method == 'action_add' && my.flag == true) {
                        my.flag = false;
                        //table树重新渲染
                        var s = {
                            id: xhr.responseJSON.result.id,
                            pId: xhr.responseJSON.result.pid,
                            add: 1,
                            productid: xhr.responseJSON.result.name[0][0],
                            ptid: xhr.responseJSON.result.product_tmpl_id,
                            name: xhr.responseJSON.result.name[0][1],
                            td: [xhr.responseJSON.result.product_spec, xhr.responseJSON.result.qty, xhr.responseJSON.result.process_id,
                                "<span class='fa fa-plus-square-o add_bom_data'></span>", "<span class='fa fa-edit new_product_edit'></span>",
                            "<span class='fa fa-trash-o new_product_delete'></span>"]
                        };
                        my.xNodes.push(s);
                        $("#treeMenu").html("");
                        var heads = ["名字", "规格", "数量", "工序", "添加", "编辑","删除"];
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
                                    productid: obj[i].product_id,
                                    name: obj[i].name,
                                    td: [obj[i].product_specs, obj[i].qty, obj[i].process_id, obj[i].product_type=='raw material'?"":"<span class='fa fa-plus-square-o add_bom_data'></span>",
                                        "<span class='fa fa-edit new_product_edit'></span>","<span class='fa fa-trash-o new_product_delete'></span>"]
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
                            productid: result.product_id,
                            name: result.name,
                            td: [result.product_specs, '', result.process_id, "<span class='fa fa-plus-square-o add_bom_data'></span>", "",""]
                        })
                        self.xNodes = tNodes;
                        var heads = ["名字", "规格", "数量", "工序", "添加", "编辑","删除"];
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