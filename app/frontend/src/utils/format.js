export const formatNumber = (number) => new Intl.NumberFormat("pt-BR").format(number || 0);

export const normalizeText = (value) => value
  .normalize("NFD")
  .replace(/[\u0300-\u036f]/g, "")
  .toLocaleLowerCase("pt-BR");
