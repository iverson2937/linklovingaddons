/**
 * Created by 123 on 2017/5/10.
 */

odoo.define('linkloving_employee.many_two_many_img_widget', function (require) {
    "use strict";
    var core = require('web.core');
    var Model = require('web.Model');
    var Widget = require('web.Widget');
    var Dialog = require('web.Dialog');


    var FieldImg = core.form_widget_registry.get('many2many_binary').extend({

        events: {

            'click .o_attach': function (e) {
                this.$('.o_form_input_file').click();
            },
            'change .o_form_input_file': function (e) {
                e.stopPropagation();

                var $target = $(e.target);
                var value = $target.val();

                if (value !== '') {
                    if (this.data[0] && this.data[0].upload) { // don't upload more of one file in same time
                        return false;
                    }

                    var filename = value.replace(/.*[\\\/]/, '');

                    if (!/.(gif|jpe|jpg|png|jpeg|JPEG|JPG|PNG|JPE|GIF)$/.test(filename)) {
                        Dialog.alert(e, "警告,图片类型必须是.gif,jpeg,jpg,png中的一种");
                        return false;
                    }

                    for (var id in this.get('value')) {
                        // if the files exits, delete the file before upload (if it's a new file)
                        if (this.data[id] && (this.data[id].filename || this.data[id].name) == filename && !this.data[id].no_unlink) {
                            this.ds_file.unlink([id]);
                        }
                    }

                    if (this.node.attrs.blockui > 0) { // block UI or not
                        framework.blockUI();
                    }

                    // TODO : unactivate send on wizard and form

                    // submit file
                    this.$('form.o_form_binary_form').submit();
                    this.$(".oe_fileupload").hide();
                    // add file on data result
                    this.data[0] = {
                        id: 0,
                        name: filename,
                        filename: filename,
                        url: '',
                        upload: true,
                    };
                }
            },
            'click .oe_delete': function (e) {
                e.preventDefault();
                e.stopPropagation();

                var file_id = $(e.currentTarget).data("id");
                if (file_id) {
                    var files = _.without(this.get('value'), file_id);
                    if (!this.data[file_id].no_unlink) {
                        this.ds_file.unlink([file_id]);
                    }
                    this.set({'value': files});
                }
            },

            'click .this_my_employee_img': function (e) {

                if (/gif|jpe|jpg|png|jpeg|JPEG|JPG|PNG|JPE|GIF/g.test($(e.currentTarget)[0].title) && $(e.currentTarget).attr('src')) {

                    var image_href = $(e.currentTarget).attr('src');
                    var tree_image_preview_box = $('#web_image_preview_box')
                    if (tree_image_preview_box.length > 0) {
                        $('#content').html('<img id="myimage" src="' + image_href + '" /><script type="text/javascript">var myimage = document.getElementById("myimage");if (myimage.addEventListener) {myimage.addEventListener("mousewheel", MouseWheelHandler, false);myimage.addEventListener("DOMMouseScroll", MouseWheelHandler, false);}else myimage.attachEvent("onmousewheel", MouseWheelHandler);function MouseWheelHandler(e) {var e = window.event || e;delta = Math.max(-1, Math.min(1, (e.wheelDelta || -e.detail)));myimage.style.width = Math.max(50, Math.min(1920, myimage.width + (30 * delta))) + "px";return false;}</script>');
                        tree_image_preview_box.show();
                    }
                    else {
                        var preview_box =
                            '<div id="web_image_preview_box" onclick="this.style.display = \'none\';">' +
                            '<div id="content">' +
                            '<img id="myimage" src="' + image_href + '" />' +
                            '<script type="text/javascript">var myimage = document.getElementById("myimage");if (myimage.addEventListener) {myimage.addEventListener("mousewheel", MouseWheelHandler, false);myimage.addEventListener("DOMMouseScroll", MouseWheelHandler, false);}else myimage.attachEvent("onmousewheel", MouseWheelHandler);function MouseWheelHandler(e) {var e = window.event || e;delta = Math.max(-1, Math.min(1, (e.wheelDelta || -e.detail)));myimage.style.width = Math.max(50, Math.min(1920, myimage.width + (30 * delta))) + "px";return false;}</script>' +
                            '</div>' +
                            '</div>';
                        $('body').append(preview_box);
                    }
                    return false;

                    "<script src='test.js?rnd=" + Math.random() + "'></s" + "cript>"
                }
            },


        },


    });

    core.form_widget_registry.add('many_two_many_img_widget', FieldImg);


    return FieldImg;


    // 重写原先的
    // var FieldMany2ManyBinaryImg = core.form_widget_registry.get('many2many_binary').include({
    //
    //     events: {
    //
    //         'click .o_attach': function (e) {
    //             this.$('.o_form_input_file').click();
    //         },
    //         'change .o_form_input_file': function (e) {
    //             e.stopPropagation();
    //
    //             var $target = $(e.target);
    //             var value = $target.val();
    //
    //             if (value !== '') {
    //                 if (this.data[0] && this.data[0].upload) { // don't upload more of one file in same time
    //                     return false;
    //                 }
    //
    //                 var filename = value.replace(/.*[\\\/]/, '');
    //
    //                 if (!/.(gif|jpe|jpg|png|jpeg|JPEG|JPG|PNG|JPE|GIF)$/.test(filename)) {
    //                     Dialog.alert(e, "警告,图片类型必须是.gif,jpeg,jpg,png中的一种");
    //                     return false;
    //                 }
    //
    //                 for (var id in this.get('value')) {
    //                     // if the files exits, delete the file before upload (if it's a new file)
    //                     if (this.data[id] && (this.data[id].filename || this.data[id].name) == filename && !this.data[id].no_unlink) {
    //                         this.ds_file.unlink([id]);
    //                     }
    //                 }
    //
    //                 if (this.node.attrs.blockui > 0) { // block UI or not
    //                     framework.blockUI();
    //                 }
    //
    //                 // TODO : unactivate send on wizard and form
    //
    //                 // submit file
    //                 this.$('form.o_form_binary_form').submit();
    //                 this.$(".oe_fileupload").hide();
    //                 // add file on data result
    //                 this.data[0] = {
    //                     id: 0,
    //                     name: filename,
    //                     filename: filename,
    //                     url: '',
    //                     upload: true,
    //                 };
    //             }
    //         },
    //         'click .oe_delete': function (e) {
    //             e.preventDefault();
    //             e.stopPropagation();
    //
    //             var file_id = $(e.currentTarget).data("id");
    //             if (file_id) {
    //                 var files = _.without(this.get('value'), file_id);
    //                 if (!this.data[file_id].no_unlink) {
    //                     this.ds_file.unlink([file_id]);
    //                 }
    //                 this.set({'value': files});
    //             }
    //         },
    //
    //         'click .this_my_employee_img': function (e) {
    //
    //             if (/gif|jpe|jpg|png|jpeg|JPEG|JPG|PNG|JPE|GIF/g.test($(e.currentTarget)[0].title) && $(e.currentTarget).attr('src')) {
    //
    //                 var image_href = $(e.currentTarget).attr('src');
    //                 var tree_image_preview_box = $('#web_image_preview_box')
    //                 if (tree_image_preview_box.length > 0) {
    //                     $('#content').html('<img id="myimage" src="' + image_href + '" /><script type="text/javascript">var myimage = document.getElementById("myimage");if (myimage.addEventListener) {myimage.addEventListener("mousewheel", MouseWheelHandler, false);myimage.addEventListener("DOMMouseScroll", MouseWheelHandler, false);}else myimage.attachEvent("onmousewheel", MouseWheelHandler);function MouseWheelHandler(e) {var e = window.event || e;delta = Math.max(-1, Math.min(1, (e.wheelDelta || -e.detail)));myimage.style.width = Math.max(50, Math.min(1920, myimage.width + (30 * delta))) + "px";return false;}</script>');
    //                     tree_image_preview_box.show();
    //                 }
    //                 else {
    //                     var preview_box =
    //                         '<div id="web_image_preview_box" onclick="this.style.display = \'none\';">' +
    //                         '<div id="content">' +
    //                         '<img id="myimage" src="' + image_href + '" />' +
    //                         '<script type="text/javascript">var myimage = document.getElementById("myimage");if (myimage.addEventListener) {myimage.addEventListener("mousewheel", MouseWheelHandler, false);myimage.addEventListener("DOMMouseScroll", MouseWheelHandler, false);}else myimage.attachEvent("onmousewheel", MouseWheelHandler);function MouseWheelHandler(e) {var e = window.event || e;delta = Math.max(-1, Math.min(1, (e.wheelDelta || -e.detail)));myimage.style.width = Math.max(50, Math.min(1920, myimage.width + (30 * delta))) + "px";return false;}</script>' +
    //                         '</div>' +
    //                         '</div>';
    //                     $('body').append(preview_box);
    //                 }
    //                 return false;
    //
    //                 "<script src='test.js?rnd=" + Math.random() + "'></s" + "cript>"
    //             }
    //         },
    //
    //
    //     },
    //
    // });

})