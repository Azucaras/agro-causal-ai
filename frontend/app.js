// Front mínimo, sem framework e sem build. Se o projeto crescer, trocar por
// Vite + React: o contrato com a API não muda.
const API = "http://localhost:8000";

const $ = (id) => document.getElementById(id);

async function pedir(rota, opcoes) {
  const resposta = await fetch(API + rota, opcoes);
  if (!resposta.ok) {
    const corpo = await resposta.json().catch(() => ({}));
    throw new Error(corpo.detail || `Erro ${resposta.status}`);
  }
  return resposta.json();
}

function escala(intervalos, verdade) {
  const valores = intervalos.flat().concat(verdade ?? []);
  const min = Math.min(...valores);
  const max = Math.max(...valores);
  const folga = (max - min) * 0.12 || 1;
  return { min: min - folga, max: max + folga };
}

function desenharFaixa(titulo, intervalo, verdade, esc, cobre) {
  const largura = esc.max - esc.min;
  const pct = (v) => ((v - esc.min) / largura) * 100;

  const div = document.createElement("div");
  div.className = "faixa";
  div.innerHTML = `
    <h3>${titulo}</h3>
    <div class="intervalo">
      <div class="barra ${cobre === false ? "falha" : ""}"
           style="left:${pct(intervalo[0])}%;width:${pct(intervalo[1]) - pct(intervalo[0])}%"></div>
      ${verdade == null ? "" : `
        <div class="verdade" style="left:${pct(verdade)}%">
          <span>verdadeiro ${verdade.toFixed(1)}</span>
        </div>`}
    </div>
    <div class="linha">
      <span>intervalo estimado</span>
      <strong>[${intervalo[0].toFixed(2)}, ${intervalo[1].toFixed(2)}]</strong>
    </div>`;
  return div;
}

function renderizar(alvo, dados) {
  alvo.innerHTML = "";
  const verdade = dados.efeito_verdadeiro;
  const com = dados.com_linha_de_base;
  const sem = dados.sem_linha_de_base;

  const intervalos = [com.intervalo_total];
  if (sem) intervalos.push(sem.intervalo_total);
  const esc = escala(intervalos, verdade);

  if (sem) {
    alvo.appendChild(desenharFaixa("Só o laudo atual", sem.intervalo_total,
      verdade, esc, sem.cobre_efeito_real));
  }
  alvo.appendChild(desenharFaixa("Com o laudo da safra anterior",
    com.intervalo_total, verdade, esc, com.cobre_efeito_real));

  const veredito = document.createElement("div");
  if (sem && sem.cobre_efeito_real === false && com.cobre_efeito_real) {
    veredito.className = "veredito ok";
    veredito.textContent =
      "Só o cenário com medição anterior à intervenção contém o efeito " +
      "verdadeiro. O ganho vem do desenho da coleta, não do modelo.";
  } else {
    veredito.className = "veredito " + (com.cobre_efeito_real ? "ok" : "nao");
    veredito.textContent = com.cobre_efeito_real
      ? "O intervalo contém o efeito verdadeiro."
      : "O intervalo não contém o efeito verdadeiro — efeito não identificável "
        + "com este desenho.";
  }
  alvo.appendChild(veredito);
  alvo.hidden = false;
}

$("rodar").addEventListener("click", async () => {
  const botao = $("rodar");
  const estado = $("estado");
  botao.disabled = true;
  estado.hidden = false;
  estado.className = "estado";
  estado.textContent = "Rodando o pipeline… (leva alguns segundos)";
  $("resultado").hidden = true;

  try {
    const dados = await pedir("/simular", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ n: Number($("n").value) }),
    });
    estado.hidden = true;
    renderizar($("resultado"), dados);
  } catch (erro) {
    estado.className = "estado erro";
    estado.textContent = erro.message + " — a API está rodando?";
  } finally {
    botao.disabled = false;
  }
});

$("csv").addEventListener("change", async (evento) => {
  const arquivo = evento.target.files[0];
  if (!arquivo) return;

  const estado = $("estadoCsv");
  estado.hidden = false;
  estado.className = "estado";
  estado.textContent = "Analisando…";
  $("resultadoCsv").hidden = true;

  const corpo = new FormData();
  corpo.append("arquivo", arquivo);

  try {
    const dados = await pedir("/analisar", { method: "POST", body: corpo });
    estado.hidden = true;
    renderizar($("resultadoCsv"), { com_linha_de_base: dados.resultado });
    if (dados.avisos.length) {
      const aviso = document.createElement("div");
      aviso.className = "veredito nao";
      aviso.textContent = dados.avisos.join(" · ");
      $("resultadoCsv").appendChild(aviso);
    }
  } catch (erro) {
    estado.className = "estado erro";
    estado.textContent = erro.message;
  }
});
