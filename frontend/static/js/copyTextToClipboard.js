// function is made globally available
window.copyTextToClipboard = (element, id) => {
    // use copy own copy2clipboard-function
    copyToClipboard(element);
    // remove all "copied successfully"-classes from other elements
    // potential side-effects if this class is used else where!
    let allSuccessfullElements = htmx.findAll('.text-success');
    allSuccessfullElements.forEach(el => {
        htmx.removeClass(el, 'text-success');
        htmx.removeClass(el, 'bi-clipboard-check-fill');
        htmx.addClass(el, 'bi-clipboard');
    });
    // add "copied successfully"-classes to element
    htmx.removeClass(`#clipboard_${id}`, 'bi-clipboard');
    htmx.addClass(`#clipboard_${id}`, 'bi-clipboard-check-fill');
    htmx.addClass(`#clipboard_${id}`, 'text-success');
}

function copyToClipboard(from) {
    const copyText = from.getAttribute("data-copy-text")
    const copyInput = document.getElementById("clipboard_input");
    copyInput.value = copyText
    // Select the text field
    copyInput.select();
    copyInput.setSelectionRange(0, 99999); // For mobile devices

    // Copy the text inside the text field
    navigator.clipboard.writeText(copyInput.value);

}