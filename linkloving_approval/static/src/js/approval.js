/**
 * Created by 123 on 2017/6/26.
 */
odoo.define('linkloving_approval.approval_core', function (require){
    "use strict";

    var core = require('web.core');
    var Model = require('web.Model');
    var Widget = require('web.Widget');
    var Pager = require('web.Pager');
    var ListView = require('web.ListView');

    var QWeb = core.qweb;
    var _t = core._t;

    var Approval = Widget.extend({
        template:'approval_load_page',
        events:{
            'show.bs.tab .tab_toggle_a': 'approval_change_tabs',
            // '':'render_pager'
        },
        //切换选项卡时重新渲染
        approval_change_tabs:function (e) {
            var self = this;
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var approval_type = $(target).attr("data");
            console.log(approval_type);
            self.$("#approval_tab").attr("data-now-tab", approval_type);

            var model = new Model("approval.center");
            return self.get_datas(this,'product.attachment.info',approval_type);
        },

        init: function (parent, action) {
            var self = this;
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
            // this.render_pager();
            // self.render_pager=function() {
            //     var $node = $('<div/>').addClass('approval_pagination').appendTo($("#approval_tab"));
            //     if (!this.pager) {
            //         this.pager = new Pager(this, self.length, self.begin, self.limit);
            //         this.pager.appendTo($node);
            //
            //         this.pager.on('pager_changed', this, function (new_state) {
            //             var self = this;
            //             var limit_changed = (this._limit !== new_state.limit);
            //
            //             this._limit = new_state.limit;
            //             this.current_min = new_state.current_min;
            //             self.reload_content().then(function() {
            //                 // Reset the scroll position to the top on page changed only
            //                 if (!limit_changed) {
            //                     self.set_scrollTop(0);
            //                     self.trigger_up('scrollTo', {offset: 0});
            //                 }
            //             });
            //         });
            //     }
            // };
            // self.reload_content = function () {
            //     return self.get_datas('product.attachment.info', 'waiting_submit')
            //     var approval_type = 'waiting_submit';
            //     var model = new Model("approval.center");
            //     return model.call("create", [{res_model: 'product.attachment.info', type: approval_type}])
            //         .then(function (result) {
            //             model.call('get_attachment_info_by_type', [result,{offset:self.begin, limit:self.limit}])
            //                 .then(function (result) {
            //                     console.log(result);
            //                     self.$("#"+approval_type).append(QWeb.render('approval_tab_content', {result:result}));
            //                 })
            //         })
            // };
            // self.set_scrollTop=function(scrollTop) {
            //     this.scrollTop = scrollTop;
            // };
            // self.get_datas = function (res_model,approval_type) {
            //     var model = new Model("approval.center");
            //     model.call("create", [{res_model: res_model, type: approval_type}])
            //     .then(function (result) {
            //         model.call('get_attachment_info_by_type', [result,{offset:self.begin, limit:self.limit}])
            //             .then(function (result) {
            //                 console.log(result.length);
            //                 self.length = result.length;
            //                 self.$("#"+approval_type).append(QWeb.render('approval_tab_content', {result:result}));
            //                 self.render_pager();
            //                 console.log($("#approval_tab"))
            //             })
            //     })
            // };
        },
        render_pager:function() {
            var $node = $('<div/>').addClass('approval_pagination').appendTo($("#approval_tab"));
            if (!this.pager) {
                this.pager = new Pager(this, this.length, this.begin, this.limit);
                this.pager.appendTo($node);

                this.pager.on('pager_changed', this, function (new_state) {
                    var self = this;
                    var limit_changed = (this._limit !== new_state.limit);

                    this._limit = new_state.limit;
                    this.current_min = new_state.current_min;
                    self.reload_content(this).then(function () {
                       // if (!limit_changed) {
                        console.log(this)
                        $('body').scrollTop(0);
                            // this.set_scrollTop(0);
                            // this.trigger_up('scrollTo', {offset: 0});
                        // }
                    });
                });
            }
        },
        reload_content : function (own) {
            var reloaded = $.Deferred();
            console.log(this.approval_type)
            var approval_type = own.approval_type[0][0];
            own.get_datas(own,'product.attachment.info', approval_type);
            reloaded.resolve();
            return  reloaded.promise();
            // var approval_type = own.approval_type[0][0];
            // var model = new Model("approval.center");
            // model.call("create", [{res_model: 'product.attachment.info', type: approval_type}])
            //     .then(function (result) {
            //         model.call('get_attachment_info_by_type', [result,{offset:own.begin, limit:own.limit}])
            //             .then(function (result) {
            //                 console.log(result);
            //                 self.$("#"+approval_type).append(QWeb.render('approval_tab_content', {result:result}));
            //             })
            //     })
            // return own
        },
        set_scrollTop:function(scrollTop) {
            this.scrollTop = scrollTop;
        },
        get_datas : function (own, res_model,approval_type) {
            var model = new Model("approval.center");
            model.call("create", [{res_model: res_model, type: approval_type}])
            .then(function (result) {
                model.call('get_attachment_info_by_type', [result,{offset:own.begin, limit:own.limit}])
                    .then(function (result) {
                        console.log(result.length);
                        own.length = result.length;
                        self.$("#"+approval_type).append(QWeb.render('approval_tab_content', {result:result}));
                        own.render_pager(this);
                        console.log($("#approval_tab"))
                    })
            })
        },


        start: function () {
            var self = this;
            // console.log($("body"))

            var model = new Model("approval.center");
            //var info_model = new Model("product.attachment.info")
            model.call("fields_get", ["", ['type']]).then(function (result) {
                console.log(result);
                self.approval_type = result.type.selection;
                console.log(self);
                self.$el.append(QWeb.render('approval_load_detail', {result:result.type.selection}));
            });


            return self.get_datas(this,'product.attachment.info', 'waiting_submit');

        }
    });

    core.action_registry.add('approval_core', Approval);

    return Approval;

})