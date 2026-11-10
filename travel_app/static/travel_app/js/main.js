// Сурет жүктелмесе — бір рет қана placeholder көрсетеді (шексіз error циклінсіз).
document.addEventListener('DOMContentLoaded', function () {
  var PLACEHOLDER = 'data:image/svg+xml;utf8,' + encodeURIComponent(
    '<svg xmlns="http://www.w3.org/2000/svg" width="600" height="400">' +
    '<rect width="100%" height="100%" fill="#1a1a1a"/>' +
    '<text x="50%" y="50%" fill="#8A8070" font-family="sans-serif" font-size="22" ' +
    'text-anchor="middle" dominant-baseline="middle">Сурет жоқ</text></svg>'
  );
  document.querySelectorAll('img').forEach(function (img) {
    img.addEventListener('error', function () {
      if (this.dataset.fallback) return;     // қайта-қайта іске қосылмауы үшін
      this.dataset.fallback = '1';
      this.src = PLACEHOLDER;
      this.alt = 'Сурет жоқ';
    });
  });
});
