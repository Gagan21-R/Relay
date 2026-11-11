import en from "./en.json";
import kn from "./kn.json";
import hi from "./hi.json";

// Every UI string must exist in all three shipped languages, so switching never shows a raw key.
function keys(o: any, p = ""): string[] {
  return Object.entries(o).flatMap(([k, v]) => (typeof v === "object" ? keys(v, `${p}${k}.`) : [`${p}${k}`]));
}

describe("UI translations", () => {
  const base = keys(en).sort();
  it.each([["kn", kn], ["hi", hi]])("%s has every English key", (_, dict) => {
    expect(keys(dict).sort()).toEqual(base);
  });
  it("ships the assistant UI in every language", () => {
    expect(kn.assistant.explain).toBeTruthy();
    expect(hi.assistant.explain).toBeTruthy();
  });
});
