(function(a){function d(b){var c=b||window.event,d=[].slice.call(arguments,1),e=0,f=!0,g=0,h=0;return b=a.event.fix(c),b.type="mousewheel",c.wheelDelta&&(e=c.wheelDelta/120),c.detail&&(e=-c.detail/3),h=e,c.axis!==undefined&&c.axis===c.HORIZONTAL_AXIS&&(h=0,g=-1*e),c.wheelDeltaY!==undefined&&(h=c.wheelDeltaY/120),c.wheelDeltaX!==undefined&&(g=-1*c.wheelDeltaX/120),d.unshift(b,e,g,h),(a.event.dispatch||a.event.handle).apply(this,d)}var b=["DOMMouseScroll","mousewheel"];if(a.event.fixHooks)for(var c=b.length;c;)a.event.fixHooks[b[--c]]=a.event.mouseHooks;a.event.special.mousewheel={setup:function(){if(this.addEventListener)for(var a=b.length;a;)this.addEventListener(b[--a],d,!1);else this.onmousewheel=d},teardown:function(){if(this.removeEventListener)for(var a=b.length;a;)this.removeEventListener(b[--a],d,!1);else this.onmousewheel=null}},a.fn.extend({mousewheel:function(a){return a?this.bind("mousewheel",a):this.trigger("mousewheel")},unmousewheel:function(a){return this.unbind("mousewheel",a)}})})(jQuery)


odoo.define('web.tree_image_preview', function (require) {
    "use strict";
    var core = require('web.core');
    var session = require('web.session');
    var ListView = require('web.ListView');
    var QWeb = core.qweb;
    var list_widget_registry = core.list_widget_registry;
    var WebTreeImagePreview = list_widget_registry.get('field.binary').extend({
        format: function (row_data, options) {
            if (!row_data[this.id] || !row_data[this.id].value) {
                return '';
            }
            var value = row_data[this.id].value, src;
            if (this.type === 'binary') {
                if (value && value.substr(0, 10).indexOf(' ') === -1) {
                    src = "data:image/png;base64," + value;
                } else {
                    var imageArgs = {
                        model: options.model,
                        field: this.id,
                        id: options.id
                    }
                    if (this.resize) {
                        imageArgs.resize = this.resize;
                    }
                    src = session.url('/web/binary/image', imageArgs);
                }
            } else {
                if (!/\//.test(row_data[this.id].value)) {
                    src = '/web/static/src/img/icons/' + row_data[this.id].value + '.png';
                } else {
                    src = row_data[this.id].value;
                }
            }
            return QWeb.render('ListView.row.image.preview', {widget: this, src: src});
        }
    });

    ListView.List.include({
        render: function () {
            var result = this._super(this, arguments)
            this.$current.delegate('img.web_tree_image_preview',
                'click', function () {
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
                });
            return result;
        },
    });
    
    list_widget_registry.add('field.tree-image-preview', WebTreeImagePreview)
});
