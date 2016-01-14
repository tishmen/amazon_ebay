django.jQuery(document).ready(function($) {

if ($('#id_itemreview_set-0-category_search').attr('readonly') != 'readonly') {
    $('#id_itemreview_set-0-category_search').after('<button id="search_button" type="button">Search</button>');
  }

  $.get('/search/' + $('#id_itemreview_set-0-category_search').val(), function(data) {
    $('#id_itemreview_set-0-category_id').html(data);
    $('#id_itemreview_set-0-category_name').val($('#id_itemreview_set-0-category_id option:first').text());
  });

  $('#search_button').bind('click', function () {
    $.get('/search/' + $('#id_itemreview_set-0-category_search').val(), function(data) {
        $('#id_itemreview_set-0-category_id').html(data);
        $('#id_itemreview_set-0-category_name').val($('#id_itemreview_set-0-category_id option:first').text());
    });
  });

  $('#id_itemreview_set-0-category_id').bind('click', function () {
    $('#id_itemreview_set-0-category_name').val($('#id_itemreview_set-0-category_id option:selected').text());
  });

});
