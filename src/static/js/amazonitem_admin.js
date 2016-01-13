django.jQuery(document).ready(function($) {

  /* add search button if search input not readonly */
  if ($('#id_itemreview_set-0-category_search').attr('readonly') != 'readonly') {
    $('#id_itemreview_set-0-category_search').after('<button id="search_button" type="button">Search</button>');
  }

  /* load options on ready if there are no options */
  if ($('#id_itemreview_set-0-category_id option').length == 0) {
    $.get('/search/' + $('#id_itemreview_set-0-category_search').val(), function(data) {
      $('#id_itemreview_set-0-category_id').html(data);
        $('#id_itemreview_set-0-category_name').val($('#id_itemreview_set-0-category_id option:first').text());
    });
  }

  /* load options on search button click */
  $('#search_button').bind('click', function () {
    $.get('/search/' + $('#id_itemreview_set-0-category_search').val(), function(data) {
        $('#id_itemreview_set-0-category_id').html(data);
        $('#id_itemreview_set-0-category_name').val($('#id_itemreview_set-0-category_id option:first').text());
    });
  });

  /* change category name hidden field on select */
  $('#id_itemreview_set-0-category_id').bind('click', function () {
    $('#id_itemreview_set-0-category_name').val($('#id_itemreview_set-0-category_id option:selected').text());
  });

  /* change char count on keyup */
  $('#id_itemreview_set-0-title').bind('keydown keyup', function () {
    $('#id_itemreview_set-0-title + .help').html($('#id_itemreview_set-0-title').val().length + ' characters');
  });

});
