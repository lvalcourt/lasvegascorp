export type SortDirection = "asc" | "desc";

function comparePrimitive(left: unknown, right: unknown) {
  const a = left ?? "";
  const b = right ?? "";

  if (typeof a === "number" && typeof b === "number") {
    return a - b;
  }

  const aText = String(a).trim();
  const bText = String(b).trim();

  const aNum = Number(aText);
  const bNum = Number(bText);
  const bothNumbers = aText !== "" && bText !== "" && !Number.isNaN(aNum) && !Number.isNaN(bNum);
  if (bothNumbers) {
    return aNum - bNum;
  }

  return aText.localeCompare(bText, undefined, { sensitivity: "base", numeric: true });
}

export function sortRows<T extends Record<string, any>>(rows: T[], key: string, direction: SortDirection) {
  const sorted = [...rows].sort((left, right) => comparePrimitive(left[key], right[key]));
  return direction === "desc" ? sorted.reverse() : sorted;
}
