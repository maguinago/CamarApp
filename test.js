let comissoesLoaded = false;

function loadComissoes(deputadoId) {
if (comissoesLoaded) return;

fetch(`https://dadosabertos.camara.leg.br/api/v2/deputados/${deputadoId}/comissoes`)
  .then(response => response.json())
  .then(data => {
    const container = document.getElementById('comissoes-container');
    container.innerHTML = '';

    if (data.dados.length === 0) {
      container.innerHTML = '<p>Este deputado não participa de nenhuma comissão atualmente.</p>';
      return;
    }

    const list = document.createElement('ul');
    list.classList.add('list-group');

    data.dados.forEach(comissao => {
      const item = document.createElement('li');
      item.className = 'list-group-item';
      item.innerText = comissao.nome;
      list.appendChild(item);
    });

    container.appendChild(list);
    comissoesLoaded = true;
  })
  .catch(error => {
    const container = document.getElementById('comissoes-container');
    container.innerHTML = '<p class="text-danger">Erro ao carregar comissões.</p>';
    console.error(error);
  });
}
