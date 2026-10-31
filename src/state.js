// Maquina de estados da revisao. REGRA CENTRAL: editar NUNCA aprova.
export const STATUSES = ["pending", "edited", "approved", "discarded"];

const TRANSITIONS = {
  pending:   { approve: "approved", discard: "discarded", edit: "edited" },
  edited:    { approve: "approved", discard: "discarded", edit: "edited" },
  approved:  { edit: "edited", discard: "discarded" },
  discarded: { approve: "approved", edit: "edited" }
};

export function applyAction(status, action) {
  const next = TRANSITIONS[status] && TRANSITIONS[status][action];
  if (!next) throw new Error("Transicao invalida: " + status + " --" + action + "-->");
  return { status: next };
}
