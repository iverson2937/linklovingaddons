/**
 * Created by 123 on 2017/5/10.
 */
odoo.define('linkloving_bom_update.bom_update', function (require) {
    "use strict";

    var core = require('web.core');
    var Model = require('web.Model');
    var Widget = require('web.Widget');

    var QWeb = core.qweb;
    var _t = core._t;

    var BomUpdate = Widget.extend({
        template:'bom_wraper',
        events:{
            'click .click_bom_tag_a': 'show_bom_lists',
        },
        show_bom_lists:function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            if(target.childNodes.length > 1){
                if(target.childNodes[1].classList.contains("fa-caret-right")){
                    target.childNodes[1].classList.remove("fa-caret-right");
                    target.childNodes[1].classList.add("fa-caret-down");
                }else if(target.childNodes[1].classList.contains("fa-caret-down")){
                    target.childNodes[1].classList.remove("fa-caret-down");
                    target.childNodes[1].classList.add("fa-caret-right");
                }
            }
            if(target.classList.contains('open-sign')){
                if(target.classList.contains("fa-caret-right")){
                    target.classList.remove("fa-caret-right");
                    target.classList.add("fa-caret-down");
                }else if(target.classList.contains("fa-caret-down")){
                    target.classList.remove("fa-caret-down");
                    target.classList.add("fa-caret-right");
                }
                target = target.parentNode;
            }
        },

        init: function (parent, action) {
            this._super.apply(this, arguments);
            this.bom_id = action.bom_id;
            var self = this;
        },
        start: function () {
            var self = this;
            if (this.bom_id) {
                return new Model("mrp.bom")
                    .call("get_bom", [this.bom_id])
                    .then(function (result) {
                        console.log(result);

                        self.$el.append(QWeb.render('bom_tree',{result:result}))
                    })
            }
        }


    })

    core.action_registry.add('bom_update', BomUpdate);

    return BomUpdate;
})