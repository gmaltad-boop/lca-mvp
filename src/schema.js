// LCA MVP — schema da resposta (Structured Outputs, strict) + validação defensiva.
export const SCHEMA = {
  type: "object",
  additionalProperties: false,
  properties: {
    patient_memory: { type: "array", items: { type: "string" } },
    observed_facts: { type: "array", items: { type: "string" } },
    professional_hypotheses: { type: "array", items: { type: "string" } },
    information_gaps: { type: "array", items: { type: "string" } },
    revisable_clinical_evolution: { type: "array", items: { type: "string" } },
    reminders: { type: "array", items: { type: "string" } },
    follow_up_questions: { type: "array", items: { type: "string" } },
    patient_goal: { type: ["string", "null"] },
    goal_progress: {
      type: "array",
      items: {
        type: "object",
        additionalProperties: false,
        properties: {
          criterion: { type: "string" },
          status: { type: "string", enum: ["avancou", "estagnou", "regrediu", "sem_dado"] }
        },
        required: ["criterion", "status"]
      }
    },
    new_achievements: { type: "array", items: { type: "string" } },
    safety_note: { type: "string" }
  },
  required: [
    "patient_memory", "observed_facts", "professional_hypotheses", "information_gaps",
    "revisable_clinical_evolution", "reminders", "follow_up_questions", "patient_goal",
    "goal_progress", "new_achievements", "safety_note"
  ]
};

export const SYSTEM_PROMPT = [
  "Voce apoia fisioterapeutas organizando notas clinicas de um prototipo. Voce NAO decide condutas,",
  "NAO diagnostica e NAO inventa dados. Regras obrigatorias:",
  "1. Nao infira alem do que consta na nota; preserve valores, prazos e negacoes exatamente.",
  "2. Separe relato do paciente (atribua: 'relata', 'refere') de observacao do profissional em todos os itens.",
  "3. professional_hypotheses: apenas hipoteses ja escritas pelo profissional na nota; se nao houver,",
  "   retorne o array com um unico item: 'nenhuma hipotese registrada'.",
  "4. information_gaps: o que falta na nota; distinga 'nao informado' de 'nao avaliado' de 'ausente';",
  "   instrumentos a considerar so aparecem rotulados como 'instrumentos a considerar (sugestao)', sem prescrever.",
  "5. revisable_clinical_evolution: rascunho em frases curtas, 1a pessoa do profissional, pronto para colar;",
  "   separa fato constatado de hipotese (hipotese sempre com 'em avaliacao').",
  "6. reminders: itens objetivos para a proxima sessao, derivados da nota.",
  "7. follow_up_questions: rascunho de mensagens/perguntas para o paciente; recupera apenas orientacoes",
  "   ja registradas na nota; usa prazos verbatim (ex.: '24h'); nao cria orientacao nova nem escolhe frequencia;",
  "   sem objetivo cadastrado, nao vincula a objetivo.",
  "8. new_achievements: melhorias relatadas/observadas nesta nota, amarradas ao que mudou; se nenhuma, array vazio.",
  "9. patient_goal: use o objetivo cadastrado fornecido; se nenhum, null e acrescente em information_gaps:",
  "   'objetivo do paciente nao informado - registrar nas palavras do paciente'. Nao proponha candidatos.",
  "10. goal_progress: somente se patient_goal for diferente de null; um item por criterio com suporte EXPLICITO",
  "    na nota; sem suporte, status 'sem_dado'; nunca invente progresso.",
  "11. patient_memory: ate 5 pontos duraveis sobre o paciente derivados desta nota (condicao, linha de base,",
  "    itens que continuam valendo); nada pontual da sessao.",
  "12. safety_note: uma frase curta lembrando que o rascunho e sujeito a revisao e validacao do profissional responsavel."
].join(" ");

export function validateOutput(o) {
  const arrKeys = ["patient_memory", "observed_facts", "professional_hypotheses", "information_gaps",
    "revisable_clinical_evolution", "reminders", "follow_up_questions", "new_achievements"];
  for (const k of arrKeys) if (!Array.isArray(o[k])) throw new Error("Campo invalido: " + k);
  if (typeof o.safety_note !== "string") throw new Error("Campo invalido: safety_note");
  if (!(o.patient_goal === null || typeof o.patient_goal === "string")) throw new Error("Campo invalido: patient_goal");
  if (!Array.isArray(o.goal_progress)) throw new Error("Campo invalido: goal_progress");
  const allowed = new Set(["avancou", "estagnou", "regrediu", "sem_dado"]);
  for (const g of o.goal_progress) {
    if (typeof g.criterion !== "string" || !allowed.has(g.status)) throw new Error("goal_progress invalido");
  }
  return o;
}
