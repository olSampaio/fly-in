from dataclasses import dataclass


@dataclass(frozen=True)
class Connection:
    zone_a: str
    zone_b: str
    max_link_capacity: int = 1

    @property
    def name(self) -> str:
        return f"{self.zone_a}-{self.zone_b}"

    @property
    def key(self) -> frozenset[str]:
        return frozenset((self.zone_a, self.zone_b))

    def other(self, zone: str) -> str:
        return self.zone_b if zone == self.zone_a else self.zone_a
