from dataclasses import dataclass, field
from typing import Any


@dataclass
class Element:
    type: str
    props: dict[str, Any]
    children: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type, "props": self.props, "children": self.children}


@dataclass
class Spec:
    root: str
    elements: dict[str, Element]

    def __post_init__(self) -> None:
        if self.root not in self.elements:
            keys = list(self.elements.keys())
            raise ValueError(f"root '{self.root}' not found in elements keys: {keys}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": self.root,
            "elements": {key: elem.to_dict() for key, elem in self.elements.items()},
        }
