/**
 * Created by 123 on 2017/6/26.
 */
odoo.define('linkloving_approval.approval_core', function (require) {
    "use strict";
    var data_manager = require('web.data_manager');
    var core = require('web.core');
    var Model = require('web.Model');
    var Widget = require('web.Widget');
    var Pager = require('web.Pager');
    var ListView = require('web.ListView');
    var Dialog = require('web.Dialog');
    var data = require('web.data');
    var pyeval = require('web.pyeval');

    var pdm_mange = require('linkloving_pdm.document_manage');


    var ViewManager = require('web.ViewManager');

    var SearchView = require('web.SearchView');

    var QWeb = core.qweb;
    var _t = core._t;
    var framework = require('web.framework');
    var PROXY_URL = "http://localhost:8088/";

    var Approval = Widget.extend({
        template: 'approval_load_page',
        events: {
            'show.bs.tab .tab_toggle_a': 'approval_change_tabs',
            'click .document_manage_btn': 'document_form_pop',
            'change .document_modify': 'document_modify_fn',
            'click .approval_product_name': 'product_pop',
            'click .review_cancel': 'cancel_approval',
            'click .document_download': 'document_download_fn',
            'click .download_file': 'document_download_fn',
            'click .document_modify_2': 'document_modify_2_fn',

            'click input.o_chat_header_file': 'on_click_inputs_file',
            'click button.download_document_checked': 'on_click_btn_download_file1',
            'click button.delect_document_checked': 'on_click_btn_delect_file',
            'click .create_file_document_btn': 'create_file_document_fn',
            'click .document_all_checkbox': 'document_all_checkbox_realize',
            'click .outage_document_file': 'outage_document_file_fn',
        },
        get_default_pdm_intranet_ip: function (then_cb) {
            var m_fields = ['pdm_intranet_ip', 'pdm_external_ip', 'pdm_port', 'op_path', 'pdm_account', 'pdm_pwd']
            return new Model("pdm.config.settings")
                .call("get_default_pdm_intranet_ip", [m_fields])
                .then(function (res) {
                    then_cb(res);
                });
        },
        // 停用
        outage_document_file_fn: function (e) {
            var tar = this;
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var approval_type = $("#approval_tab").attr("data-now-tab");
            var new_file_id = $(target).parents(".tab_pane_display").attr("data-id");
            var state_type = $(target).attr("data");
            new Model("product.attachment.info").call("chenge_outage_state", [new_file_id], {
                state_type: state_type,
                new_file_id: new_file_id
            })
                .then(function (result_info) {
                    console.log(result_info.state)
                    return tar.get_datas(tar, 'product.attachment.info', approval_type);
                });
        },

        create_file_document_fn: function (e) {
            var tar = this;

            var e = e || window.event;
            var target = e.target || e.srcElement;

            var action = {
                name: "详细",
                type: 'ir.actions.act_window',
                res_model: 'product.attachment.info',
                view_type: 'form',
                view_mode: 'tree,form',
                views: [[false, 'form']],
                target: "new"
            };

            this.do_action(action);
            self.$(document).ajaxComplete(function (event, xhr, settings) {
                if (settings.data) {
                    var data = JSON.parse(settings.data)
                    if (data.params.model == 'product.attachment.info') {
                        if (data.params.method == 'action_create_many_info') {
                            var approval_type = self.$("#approval_tab").attr("data-now-tab");
                            self.$("#" + approval_type).html("");
                            console.log(approval_type);
                            tar.file_checkbox = [];

                            $('.delect_hide').hide();

                            $("input:checked").each(function () {
                                $(this).prop('checked', false);
                            });
                            return tar.get_datas(tar, 'product.attachment.info', approval_type);
                        }
                    }

                }
            })
            return tar.get_datas(tar, 'product.attachment.info', 'waiting_submit');


        },

        // 全选
        document_all_checkbox_realize: function (e) {
            var self = this;

            var e = e || window.event;
            var target = e.target || e.srcElement;
            var approval_type = $("#approval_tab").attr("data-now-tab");
            $("#" + approval_type + "  input[type='checkbox']").each(function () {
                $(this).prop('checked', $(target).prop('checked') || false);
                self.on_click_inputs_file(this, 'all_checkbox');
            });
        },


        on_click_btn_delect_file: function (e) {
            var tar = this;
            var attachment_list = [];
            var approval_type = $("#approval_tab").attr("data-now-tab");
            var choice = confirm("您确认要删除吗？", function () {
            }, null);
            if (choice) {
                if (e.target.parentNode.className == 'delect_one_document') {
                    var e = e || window.event;
                    var target = e.target || e.srcElement;
                    var new_file_id = $(target).parents(".tab_pane_display").attr("data-id");
                    console.log('删除一个' + new_file_id);
                    attachment_list.splice(0, 0, parseInt(new_file_id));
                }
                else {
                    console.log('删除选中' + tar.file_checkbox);
                    if (tar.file_checkbox) {
                        for (var i = 0; i < tar.file_checkbox.length; i++) {
                            attachment_list[i] = parseInt(tar.file_checkbox[i])
                        }
                    }
                }

                new Model("product.attachment.info")
                    .call("unlink_attachment_list", [attachment_list], {attachment_list: attachment_list})
                    .then(function (result_info) {
                        console.log(result_info);
                        $('.delect_hide').hide();
                        tar.file_checkbox = [];
                        $("input:checked").each(function () {
                            $(this).prop('checked', false);
                        });
                        return tar.get_datas(tar, 'product.attachment.info', approval_type);
                    });
            }
        },


        on_click_btn_download_file1: function (e) {
            var self = this;
            var attachment_local_list = [];
            for (let i = 0; i < self.file_checkbox.length; i++) {
                var target = e.target || e.srcElement;
                var new_file_id = parseInt(self.file_checkbox[i]);
                var dom = this.$('div[data-id=' + parseInt(self.file_checkbox[i]) + ']')
                var type = dom.attr("data").toUpperCase();
                if (type == 'OTHER' || type == 'DESIGN') {
                    self.batch_download_file(new_file_id, dom, target);
                }
                else {
                    attachment_local_list.splice(0, 0, parseInt(self.file_checkbox[i]));
                }
            }
            if (attachment_local_list.length > 0)
                window.location.href = "/linkloving_approval/all_download_file?download=true&filename=file_download.zip&file_list=" + attachment_local_list;

            $('.delect_hide').hide();
            self.file_checkbox = [];
            //    查找页面所有checkbox 取消选中
            $("input:checked").each(function () {
                $(this).prop('checked', false);
            });
        },

        batch_download_file: function (new_file_id, dom, target) {
            var self = this;
            var remote_path = dom.find(".remote_path").text();
            if (remote_path[0] == '/') {
                remote_path[0] = '';
            }
            console.log(remote_path);
            $.ajax({
                type: "GET",
                url: PROXY_URL + "downloadfile",
                data: $.extend(self.pdm_info, {remotefile: remote_path}),// "http://localhost:8088/downloadfile?remotefile=" + remote_path,
                success: function (data) {
                    console.log(data);
                    if (data.result == '1') {
                        Dialog.alert(target, "已下载至指定目录");
                    }
                    else if (data.result == '2') {
                        Dialog.alert(target, "下载失败, 未选择存储路径");
                    }
                    else {
                        Dialog.alert(target, "下载失败");
                    }
                },
                error: function (error) {
                    Dialog.alert(target, "下载失败,请检查是否打开了代理软件");
                }
            })
        },

        on_click_inputs_file: function (event, top_10) {
            var self = this;
            var is_hava = true;
            var input_content;

            top_10 ? input_content = event : input_content = event.target;

            var approval_type = $("#approval_tab").attr("data-now-tab");

            if ($(input_content).prop("checked")) {
                self.file_checkbox.splice(0, 0, input_content.name);
            } else {
                while (is_hava) {
                    if ($.inArray(input_content.name, self.file_checkbox) >= 0)
                        self.file_checkbox.splice($.inArray(input_content.name, self.file_checkbox), 1);
                    else
                        break;
                }
            }
            self.file_checkbox = $.grep(self.file_checkbox, function (n) {
                return $.trim(n).length > 0;
            });
            console.log(self.file_checkbox)
            if (self.file_checkbox.length > 1)
                if (approval_type == 'submitted' || approval_type == 'approval')
                    $('#download_checkbox').show();
                else {
                    $('.delect_hide').show();
                    if (approval_type == 'waiting_approval')
                        $('#delect_checkbox').hide();
                }


            else if (self.file_checkbox.length = 1)
                $('.delect_hide').hide();
        },

        document_modify_2_fn: function (e) {
            var self = this;
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var default_code = $(target).parents(".tab_pane_display").find(".approval_product_name").attr("default-code").trim()
            var cur_type = $(target).parents(".document_btns").find(".document_download").attr("data");
            var ret = $(target).parents(".tab_pane_display").find(".version_span").text()
            var remote_file = cur_type.toUpperCase() + '/' + default_code.split('.').join('/') + '/v' + ret +
                '/' + cur_type.toUpperCase() + '_' + default_code.split('.').join('_') + '_v' + ret
            console.log(ret);
            $.ajax({
                type: "GET",
                url: PROXY_URL + "uploadfile",//http://localhost:8088/uploadfile?id=" + this.product_id + "&remotefile=" + remote_file,
                data: $.extend(self.pdm_info, {id: this.product_id, remotefile: remote_file}),// "http://localhost:8088/downloadfile?remotefile=" + remote_path,
                success: function (data) {
                    framework.unblockUI();
                    console.log(data);
                    if (data.result == '1') {
                        $(target).parents(".tab_pane_display").children(".tab_message_display").prepend("<div class='document_modify_name'>新修改的文件：<span>" + data.choose_file_name + "</span></div>");
                        var new_file_id = $(target).parents(".tab_pane_display").attr("data-id");
                        console.log(data);
                        return new Model("product.attachment.info")
                            .call("update_attachment", [parseInt(new_file_id)], {remote_path: data.path})
                            .then(function (result) {
                                Dialog.alert(target, "修改成功");
                            })
                        //$(".my_load_file_name").val(data.choose_file_name)
                        //$(".my_load_file_remote_path").val(data.path)
                    }
                },
                error: function (error) {
                    framework.unblockUI();
                    Dialog.alert(target, "上传失败,请打开代理软件");
                    console.log(error);
                }
            })

        },
        //下载
        document_download_fn: function (e) {
            var self = this;
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var new_file_id = $(target).parents(".tab_pane_display").attr("data-id");
            // console.log(new_file_id)
            console.log($(target))
            var type = $(target).attr("data").toUpperCase()
            var remote_path = $(target).parents(".tab_pane_display").find(".remote_path").text()

            if (remote_path[0] == '/') {
                remote_path[0] = '';
            }
            console.log(remote_path)
            if (type == 'OTHER' || type == 'DESIGN') {
                $.ajax({
                    type: "GET",
                    url: PROXY_URL + "downloadfile",// "http://localhost:8088/downloadfile?remotefile=" + remote_path,
                    data: $.extend(self.pdm_info, {remotefile: remote_path}),// "http://localhost:8088/downloadfile?remotefile=" + remote_path,
                    success: function (data) {
                        console.log(data);
                        if (data.result == '1') {
                            Dialog.alert(target, "已下载至指定目录");
                        }
                        else if (data.result == '2') {
                            Dialog.alert(target, "下载失败, 未选择存储路径");
                        }
                        else {
                            Dialog.alert(target, "下载失败");
                        }
                    },
                    error: function (error) {
                        Dialog.alert(target, "下载失败,请检查是否打开了代理软件");
                    }
                })
            } else {
                window.location.href = '/download_file/?download=true&id=' + new_file_id;

            }
        },
        //取消审核
        cancel_approval: function (e) {
            var tar = this;
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var new_file_id = $(target).parents(".tab_pane_display").attr("data-id");
            var action = {
                name: "填写取消审核原因",
                type: 'ir.actions.act_window',
                res_model: 'review.process.cancel.wizard',
                view_type: 'form',
                view_mode: 'tree,form',
                views: [[false, 'form']],
                context: {'default_product_attachment_info_id': parseInt(new_file_id), 'review_type': 'file_review'},
                target: "new",
            };
            this.do_action(action);
            self.$(document).ajaxComplete(function (event, xhr, settings) {
                // "{"jsonrpc":"2.0","method":"call","params":{"model":"review.process.wizard","method":"search_read","args":[[["id","in",[10]]],["remark","partner_id","display_name","__last_update"]],"kwargs":{"context":{"lang":"zh_CN","tz":"Asia/Shanghai","uid":1,"default_product_attachment_info_id":"4","params":{},"bin_size":true,"active_test":false}}},"id":980816587}"
                // console.log(settings)
                var data = JSON.parse(settings.data)
                if (data.params.model == 'review.process.cancel.wizard') {
                    if (data.params.method == 'action_cancel_review') {
                        var file_type = self.$("#approval_tab").attr("data-now-tab");
                        var product_id = parseInt($("body").attr("data-product-id"));
                        return new Model("product.template")
                            .call("get_attachemnt_info_list", [product_id], {type: file_type})
                            .then(function (result) {
                                console.log(result);
                                self.$("#" + file_type).html("");
                                return tar.get_datas(tar, 'product.attachment.info', file_type);
                            })
                    }
                }
            })
        },
        //点击产品名弹出框
        product_pop: function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var product_id = parseInt($(target).attr('product-id'));
            var action = {
                name: "产品详细",
                type: 'ir.actions.act_window',
                res_model: 'product.template',
                view_type: 'form',
                view_mode: 'tree,form',
                views: [[false, 'form']],
                res_id: product_id,
                target: "new"
            };
            this.do_action(action);
        },
        //文件修改
        document_modify_fn: function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            console.log($(target).parents(".tab_pane_display").children(".tab_message_display"));
            $(target).parents(".tab_pane_display").children(".tab_message_display").prepend("<div class='document_modify_name'>新修改的文件：<span>" + target.files[0].name + "</span></div>");
            $(".document_modify span").val(target.files[0].name);
            var new_file_id = $(target).parents(".tab_pane_display").attr("data-id");
            console.log(new_file_id);
            console.log(target.files[0]);
            var new_file = target.files[0];

            var reader = new FileReader();
            reader.readAsDataURL(new_file);
            reader.onload = function () {
                var encoded_file = reader.result;
                var position = encoded_file.indexOf("base64,");
                if (position > -1) {
                    encoded_file = encoded_file.slice(position + "base64,".length);
                }
                // var result = btoa(encoded_file);
                return new Model("product.attachment.info")
                    .call("update_attachment", [parseInt(new_file_id)], {
                        file_binary: encoded_file,
                        file_name: new_file.name
                    })
                    .then(function (result) {
                    })
            };
        },
        //审核操作
        document_form_pop: function (e) {
            var tar = this;
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var file_id = $(target).attr("data-id");
            var is_show_action_deny = $(target).attr("data-suibian");
            var context_data;

            if (file_id) {

                context_data = {
                    'default_product_attachment_info_id': file_id,
                    'is_show_action_deny': is_show_action_deny,
                    'review_type': 'file_review',
                }

            } else {
                // var dom = this.$('div[data-id=' + parseInt(tar.file_checkbox[0]) + ']')
                // console.log(dom)

                var dom_btn = this.$('button[data-id=' + parseInt(tar.file_checkbox[0]) + ']');
                is_show_action_deny = dom_btn.attr("data-suibian");

                context_data = {
                    'is_show_action_deny': is_show_action_deny,
                    'review_type': 'file_review',
                    'file_data_list': tar.file_checkbox
                }
            }

            var action = {
                name: "详细",
                type: 'ir.actions.act_window',
                res_model: 'review.process.wizard',
                view_type: 'form',
                view_mode: 'tree,form',
                views: [[false, 'form']],
                context: context_data,
                target: "new",
            };
            this.do_action(action);
            self.$(document).ajaxComplete(function (event, xhr, settings) {
                if (settings.data) {
                    var data = JSON.parse(settings.data)
                    if (data.params.model == 'review.process.wizard') {
                        if (data.params.method == 'action_to_next' ||
                            data.params.method == 'action_pass' ||
                            data.params.method == 'action_deny'
                        ) {
                            var approval_type = self.$("#approval_tab").attr("data-now-tab");
                            self.$("#" + approval_type).html("");
                            console.log(approval_type);
                            tar.file_checkbox = [];

                            $('.delect_hide').hide();

                            $("input:checked").each(function () {
                                $(this).prop('checked', false);
                            });
                            return tar.get_datas(tar, 'product.attachment.info', approval_type);
                        }
                    }

                }
            })
        },
        //切换选项卡时重新渲染
        approval_change_tabs: function (e) {
            var self = this;
            var e = e || window.event;
            self.flag = 1;
            self.begin = 1;
            var target = e.target || e.srcElement;
            var approval_type = $(target).attr("data");
            // console.log(approval_type);
            self.$("#approval_tab").attr("data-now-tab", approval_type);

            var model = new Model("approval.center");
            self.file_checkbox = [];
            $('.delect_hide').hide();
            $('#top_all_checkbox').prop('checked', false);
            return self.get_datas(this, 'product.attachment.info', approval_type);
        },

        init: function (parent, action) {
            var self = this;
            self.flag = 1;
            self.begin = 1;
            self.limit = 15;
            this.approval_type = null;
            this._super.apply(this, arguments);
            if (action.product_id) {
                this.product_id = action.product_id;
            } else {
                this.product_id = action.params.active_id;
            }
            //分页
            this.pager = null;
            this.registry = core.view_registry;
            this.file_checkbox = new Array();
        },


        setup_search_view: function () {
            var self = this;
            if (this.searchview) {
                this.searchview.destroy();
            }

            var search_defaults = {};
            // var context = this.action.context || [];
            // _.each(context, function (value, key) {
            //     var match = /^search_default_(.*)$/.exec(key);
            //     if (match) {
            //         search_defaults[match[1]] = value;
            //     }
            // });

            var options = {
                hidden: true,
                disable_custom_filters: true,
                $buttons: $("<div>"),
                action: this.action,
                search_defaults: search_defaults,
            };
            self.dataset = new data.DataSetSearch(this, "product.attachment.info", {}, false);
            $.when(self.load_views()).done(function () {
                // Instantiate the SearchView, but do not append it nor its buttons to the DOM as this will
                // be done later, simultaneously to all other ControlPanel elements
                self.searchview = new SearchView(self, self.dataset, self.search_fields_view, options);
                var $node1 = $('<div/>').addClass('approval_searchview')
                $(".approval_page_container").prepend($node1);
                self.searchview.on('search_data', self, self.search.bind(self));
                $.when(self.searchview.appendTo($node1)).done(function () {
                    self.searchview_elements = {};
                    self.searchview_elements.$searchview = self.searchview.$el;
                    self.searchview_elements.$searchview_buttons = self.searchview.$buttons.contents();
                    self.searchview.do_show();
                });
            });

        },
        load_views: function (load_fields) {
            var self = this;
            var views = [];
            _.each(this.views, function (view) {
                if (!view.fields_view) {
                    views.push([view.view_id, view.type]);
                }
            });
            var options = {
                load_fields: load_fields,
            };
            if (!this.search_fields_view) {
                options.load_filters = true;
                views.push([false, 'search']);
            }
            return data_manager.load_views(this.dataset, views, options).then(function (fields_views) {
                _.each(fields_views, function (fields_view, view_type) {
                    if (view_type === 'search') {
                        self.search_fields_view = fields_view;
                    } else {
                        self.views[view_type].fields_view = fields_view;
                    }
                });
            });
        },
        search: function (domains, contexts, groupbys) {
            var self = this;
            var own = this;
            var approval_type = $("#approval_tab").attr("data-now-tab");
            pyeval.eval_domains_and_contexts({
                domains: [[]].concat(domains || []),
                contexts: [].concat(contexts || []),
                group_by_seq: groupbys || []
            }).done(function (results) {
                var model = new Model("approval.center");
                var res_model = 'product.attachment.info';
                model.call("create", [{res_model: res_model, type: approval_type}])
                    .then(function (result) {
                        model.call('get_attachment_info_by_types', [[result]], {
                            offset: own.begin - 1,
                            limit: own.limit,
                            domains: results.domain,
                            contexts: results.context,
                            groupbys: results.groupby
                        })
                            .then(function (result) {
                                console.log(result);
                                own.length = result.length;
                                self.$("#" + approval_type).html("");
                                self.$("#" + approval_type).append(QWeb.render('approval_tab_content', {
                                    result: result.records,
                                    approval_type: approval_type
                                }));
                                own.render_pager(this);
                            })
                    })
            })

            // var res_model = 'product.attachment.info';
            // // var approval_type = 'waiting_submit';
            // var approval_type = $("#approval_tab").attr("data-now-tab");
            // console.log($("#approval_tab").attr("data-now-tab"));
            //
            // var own = this;
            //
            //
            // var model = new Model("approval.center");
            // model.call("create", [{res_model: res_model, type: approval_type}])
            //     .then(function (result) {
            //         model.call('get_attachment_info_by_types', [result], {
            //             offset: own.begin - 1,
            //             limit: own.limit,
            //             domains: domains,
            //             contexts: contexts,
            //             groupbys: groupbys
            //         })
            //             .then(function (result) {
            //                 console.log(result);
            //                 own.length = result.length;
            //                 self.$("#" + approval_type).html("");
            //                 self.$("#" + approval_type).append(QWeb.render('approval_tab_content', {
            //                     result: result.records,
            //                     approval_type: approval_type
            //                 }));
            //                 own.render_pager(this);
            //             })
            //     })

        },
        render_pager: function () {
            if (this.flag == 1) {
                if ($(".approval_pagination")) {
                    $(".approval_pagination").remove()
                }
                var $node = $('<div/>').addClass('approval_pagination').appendTo($("#approval_tab"));
                // if (!this.pager) {
                this.pager = new Pager(this, this.length, this.begin, this.limit);
                this.pager.appendTo($node);


                this.setup_search_view();

                this.pager.on('pager_changed', this, function (new_state) {
                    var self = this;
                    var limit_changed = (this._limit !== new_state.limit);

                    this._limit = new_state.limit;
                    this.current_min = new_state.current_min;
                    self.reload_content(this).then(function () {
                        // if (!limit_changed) {
                        self.$el.animate({"scrollTop": "0px"}, 100);
                        // $(".approval_page_container").offset({ top: 50})
                        // this.set_scrollTop(0);
                        // this.trigger_up('scrollTo', {offset: 0});
                        // }
                    });
                });
                // }
                this.flag = 2;
            }
        },
        reload_content: function (own) {
            var reloaded = $.Deferred();
            // console.log(this.approval_type)
            own.begin = own.current_min;
            var approval_type = $("#approval_tab").attr("data-now-tab");
            own.get_datas(own, 'product.attachment.info', approval_type);
            reloaded.resolve();
            return reloaded.promise();
        },
        set_scrollTop: function (scrollTop) {
            this.scrollTop = scrollTop;
        },
        get_datas: function (own, res_model, approval_type) {
            var model = new Model("approval.center");
            model.call("create", [{res_model: res_model, type: approval_type}])
                .then(function (result) {
                    model.call('get_attachment_info_by_type', [result], {offset: own.begin - 1, limit: own.limit})
                        .then(function (result) {
                            console.log(result);
                            own.length = result.length;
                            self.$("#" + approval_type).html("");
                            self.$("#" + approval_type).append(QWeb.render('approval_tab_content', {
                                result: result.records,
                                approval_type: approval_type
                            }));
                            own.render_pager(this);
                        })
                })

            // var approval_type = $("#approval_tab").attr("data-now-tab");
            // if (approval_type in ['submitted', 'approval']) {
            //
            //     $("#div_file_checkbox").each(function () {
            //         $(this).hide();
            //     });
            // }
        },


        start: function () {
            var self = this;
            var model = new Model("approval.center");
            //var info_model = new Model("product.attachment.info")
            model.call("fields_get", ["", ['type']]).then(function (result) {
                console.log(result);
                self.approval_type = result.type.selection;
                // console.log(self);
                self.$el.append(QWeb.render('approval_load_detail_file', {result: result.type.selection}));
                self.get_default_pdm_intranet_ip(function (res) {
                    self.pdm_info = res;
                    console.log(res);
                })
            });
            return self.get_datas(this, 'product.attachment.info', 'waiting_submit');

        }
    });


    var FieldBinaryFile = core.form_widget_registry.get('binary');

    FieldBinaryFile.include({
        set_filename: function (value) {

            $(".this_my_filename").val(value);

            var filename = this.node.attrs.filename;
            if (filename) {
                var field = this.field_manager.fields[filename];
                if (field) {
                    field.set_value(value);
                    field._dirty_flag = true;
                }
            }
        },
    });


    core.action_registry.add('approval_core', Approval);

    return Approval;

})
