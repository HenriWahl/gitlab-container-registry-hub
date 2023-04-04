window.onscroll = function () {
    detect_scrolling()
}

function detect_scrolling() {
    if (document.body.scrollTop > 20 || document.documentElement.scrollTop > 20) {
        htmx.removeClass(htmx.find('#back_to_top'), 'visually-hidden')
    } else {
        htmx.addClass(htmx.find('#back_to_top'), 'visually-hidden')
    }
}

function scroll_back_to_top() {
    // Mozilla + Chrome
    document.documentElement.scrollTop = 0
    // Safari
    document.body.scrollTop = 0
}