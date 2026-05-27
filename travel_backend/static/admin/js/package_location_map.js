// Immediately try to modify map elements
(function() {
  console.log('SCRIPT LOADED');
  
  // Try immediately
  var mapElements = document.querySelectorAll('.tm-map-picker__map');
  console.log('Found ' + mapElements.length + ' maps');
  
  if (mapElements.length > 0) {
    mapElements[0].innerHTML = '<div style="padding: 20px; background: yellow; color: black;">MAP SCRIPT IS RUNNING!</div>';
  }
  
  // Also try with a timeout
  setTimeout(function() {
    console.log('Timeout fired');
    var maps2 = document.querySelectorAll('.tm-map-picker__map');
    if (maps2.length > 0 && maps2[0].innerHTML === '') {
      maps2[0].innerHTML = '<div style="padding: 20px; background: orange; color: black;">TIMEOUT SCRIPT RUNNING!</div>';
    }
  }, 100);
})();
