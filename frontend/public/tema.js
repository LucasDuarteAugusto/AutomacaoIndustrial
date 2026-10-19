// Aplica o tema antes da primeira pintura (evita piscar claro→escuro). Arquivo externo por causa da CSP.
(function () {
  var tema = localStorage.getItem("tema");
  var escuro = tema ? tema === "escuro" : matchMedia("(prefers-color-scheme: dark)").matches;
  document.documentElement.classList.toggle("dark", escuro);
})();
