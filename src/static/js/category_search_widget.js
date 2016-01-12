django.jQuery(document).ready(function($) {

  if ($('#id_itemreview-0-category_id option:selected').val() == '') {
    $.get("/search/" + $('#id_itemreview-0-category_search').val(), function(data) {
      $('#id_itemreview-0-category_id').html(data);
    });
  }

  $('#search_button').bind('click', function (event) {
    event.preventDefault();
    $.get("/search/" + $('#id_itemreview-0-category_search').val(), function(data) {
      $('#id_itemreview-0-category_id').html(data);
    });
  });

  $('#id_itemreview-0-category_id').bind('change', function (event) {
    ($('#id_itemreview-0-category_id option:selected').val())
  });

});

