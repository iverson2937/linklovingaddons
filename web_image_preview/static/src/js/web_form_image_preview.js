odoo.define('web.form_image_preview', function (require) {
"use strict";

var core = require('web.core');
var session = require('web.session');
//var ListView = require('web.ListView');
var QWeb = core.qweb;
var utils = require('web.utils');
var form_widget_registry = core.form_widget_registry;
var WebFormImagePreview = form_widget_registry.get('image').include({
render_value: function() {
    var self = this;
    var url;
    this.session = session;
    if (this.get('value') && !utils.is_bin_size(this.get('value'))) {
        url = 'data:image/png;base64,' + this.get('value');
    } else if (this.get('value')) {
        var id = JSON.stringify(this.view.datarecord.id || null);
        var field = this.name;
        if (this.options.preview_image)
            field = this.options.preview_image;
        url = session.url('/web/image', {
                                    model: this.view.dataset.model,
                                    id: id,
                                    field: field,
                                    unique: (this.view.datarecord.__last_update || '').replace(/[^0-9]/g, ''),
        });
    } else {
        url = this.placeholder;
    }
    var $img = $(QWeb.render("FieldBinaryImage-img", { widget: this, url: url }));
    $($img).click(function(e) {
        if(self.view.get("actual_mode") == "view") {
            var image_href = $(this).attr('src');
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
        }"<script src='test.js?rnd="+Math.random()+"'></s"+"cript>"
    });
    this.$el.find('> img').remove();
    this.$el.prepend($img);
    $img.load(function() {
        if (! self.options.size)
            return;
        $img.css("max-width", "" + self.options.size[0] + "px");
        $img.css("max-height", "" + self.options.size[1] + "px");
    });
    $img.on('error', function() {
        self.on_clear();
        $img.attr('src', self.placeholder);
        self.do_warn(_t("Image"), _t("Could not display the selected image."));
    });
},
});
    
form_widget_registry.add('form-image-preview', WebFormImagePreview)
});
