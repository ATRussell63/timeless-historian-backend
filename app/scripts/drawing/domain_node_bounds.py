from dataclasses import dataclass

@dataclass
class NodeRef:
    type: str
    ref: str | int

@dataclass
class DomainBounds:
    up: NodeRef
    down: NodeRef
    left: NodeRef
    right: NodeRef

DOMAIN_BOUNDS_GUIDE = {

    # TEMPLAR
    18: DomainBounds(up=NodeRef('name', 'Spiritual Aid'),
                        down=NodeRef('id', 0), # TODO - go hunt for this id
                        left=NodeRef('name', 'Divine Wrath'),
                        right=NodeRef('id', 0)) # TODO - go find it
}