document.addEventListener("click", function (event) {
  const el = event.target;

  const data = {
    outerHTML: el.outerHTML
  };

  fetch("/generate", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(data)
  })
    .then(response => response.json())
    .then(result => {
      document.getElementById("base").innerText = result.base;
      document.getElementById("bootstrap").innerText = result.bootstrap;
      document.getElementById("tailwind").innerText = result.tailwind;
      hljs.highlightAll();
    });
});

function copyCode(id) {
  const code = document.getElementById(id).innerText;
  navigator.clipboard.writeText(code).then(() => {
    alert("Código copiado!");
  });
}

