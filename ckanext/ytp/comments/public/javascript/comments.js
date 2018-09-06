function ShowCommentForm(id) {
    $("#" + id).removeClass('hidden');
}




$( window ).on("load", function(e) {
    $(".toggle-show > td").attr("colspan", "2");

    $(".toggle-seperator > td").attr("colspan", "2");
});