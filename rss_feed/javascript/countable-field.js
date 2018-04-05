function CountableField(field_id) {
    textarea = document.getElementById(field_id);
    countDisplay = document.getElementById(field_id + "_counter")
    if (textarea != null && countDisplay != null) {
        var minCount = textarea.getAttribute("data-min-count");
        var maxCount = textarea.getAttribute("data-max-count");

        Countable.live(textarea, updateFieldWordCount);
    }

    function updateFieldWordCount(counter) {
        countDisplay.getElementsByClassName("text-count-current")[0].innerHTML = counter.words;
        if (minCount && counter.words < minCount)
            countDisplay.className = "text-count text-is-under-min";
        else if (maxCount && counter.words > maxCount)
            countDisplay.className = "text-count text-is-over-max";
        else
            countDisplay.className = "text-count";
    }
}