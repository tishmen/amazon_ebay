django.jQuery(document).ready(function($) {

  $('#id_new_title').bind('keyup', function () {
    $('#id_new_title + .help').html($('#id_new_title').val().length + ' characters');
  });

});

