# Interfaces

PROVIDES the product's own user-facing surfaces over a spec-tree product
SO THAT humans and agents working that product
CAN inspect and manipulate the tree through purpose-built surfaces rather than raw files

## Assertions

### Compliance

- ALWAYS: source spec-tree structure and derived state from the SPX CLI's JSON projection — an interface surface never re-parses directory suffixes, assembles hierarchy, or derives node state itself ([audit])
- ALWAYS: present the node states and the node and decision categories the spec-tree methodology defines, so every surface reads the tree consistently ([audit])
