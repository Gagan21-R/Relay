import { PRIORITY_STYLE, simTime } from "./ui";

describe("score display helpers", () => {
  it("maps priority scores to P1-P4 bands", () => {
    expect(PRIORITY_STYLE(84).label).toBe("P1");
    expect(PRIORITY_STYLE(55).label).toBe("P2");
    expect(PRIORITY_STYLE(30).label).toBe("P3");
    expect(PRIORITY_STYLE(0).label).toBe("P4");
  });
  it("formats simulated time", () => {
    expect(simTime(12)).toBe("T+12.0 h");
    expect(simTime(null)).toBe("—");
  });
});
