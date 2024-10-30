"""
Class and methods for internal and external nodes in B+ Tree.
"""

import logging
import math
from typing import Self

from exceptions import *

logger = logging.getLogger(__name__)


class Node:
    """A general node in B+ Tree, type is identified by self.leaf.

    Most operations are identical for internal and external nodes, so one general
    class should be enough in this case.
    """

    def __init__(
        self,
        order: int,
        leaf: bool,
        keys: list[Self | int] = [],
        values: list[Self | int] = [],
        parent: Self | None = None,
    ) -> None:
        """Initialzie a general node.

        :param order: order of the B+ tree
        :type order: int
        :param leaf: is external node or not
        :type leaf: bool
        :param keys: keys, defaults to []
        :type keys: list[Self | int], optional
        :param values: Node for internal, integer for external, defaults to [Self | int]
        :type values: list, optional
        :param parent: node's pareent, defaults to None
        :type parent: Self | None, optional
        """
        self.order = order
        self.leaf = leaf
        self.keys = keys
        self.values = values
        self.parent = parent
        self.prev = None
        self.next = None

    def is_underflow(self) -> bool:
        """Check if the node is underflow.

        :return: True if yes, False otherwise
        :rtype: bool
        """
        return len(self.keys) < math.ceil(self.order / 2)

    def is_overflow(self) -> bool:
        """Check if the node is overflow.

        :return: True if yes, False otherwise
        :rtype: boolean
        """
        return len(self.keys) > self.order

    def add(self, data: int) -> None:
        """Add data as key-value pair into leaf node.

        The external node must have keys and values just like the internal ones to
        share some common functionalities (e.g., Node.split()), so we duplicate the
        data as a pair for consistency.

        :param data: node's parent
        :type data: int
        :param data: data to insert
        :type data: int
        """

        # simply insert a pair if node is empty
        if not self.keys:
            self.keys.append(data)
            self.values.append([data])
            return

        # insert key-value pair into right position
        for i, key in enumerate(self.keys):
            if data == key:
                print(f"Data already exists: {data}")
                return
            elif data < key:
                # insert data to the left child of existing key
                self.keys = self.keys[:i] + [data] + self.keys[i:]
                self.values = self.values[:i] + [[data]] + self.values[i:]
                return

        # if data is greater than every keys, insert into rightmost position
        self.keys.append(data)
        self.values.append([data])

    def remove(self, data: int) -> tuple[Self, int, int]:
        """Remove key-value pair in leaf node.

        :param data: data to remove
        :type data: int
        :raises RemoveError: raise when the data is not found
        :return: parent node, original min key, and new min key
        :rtype: tuple[Self, int, int]
        """
        try:
            idx = self.keys.index(data)
        except ValueError:
            print(f"Data not found: {data}")
            raise RemoveError

        old_min_key = self.keys[0]
        self.keys.pop(idx)
        self.values.pop(idx)

        new_min_key = self.keys[0] if self.keys else old_min_key
        return self.parent, old_min_key, new_min_key

    def split(self) -> None:
        """Split the node into parent, left, and child nodes."""
        logger.debug(f"SPLIT, keys: {self.keys}, values: {self.values}")

        # internal node: k + 1 values, external nodes: k values
        key_mid_idx = math.ceil(self.order / 2)
        value_mid_idx = key_mid_idx if self.leaf else key_mid_idx + 1

        left = Node(
            self.order,
            self.leaf,
            self.keys[:key_mid_idx],
            self.values[:value_mid_idx],
            self,
        )
        right = Node(
            self.order,
            self.leaf,
            self.keys[key_mid_idx:],
            self.values[value_mid_idx:],
            self,
        )

        # if it's an internal node, update grandchild's parents
        if not self.leaf:
            for child in left.values:
                child.parent = left
            for child in right.values:
                child.parent = right

        # convert itself into a new parent node
        # for internal nodes, push up instead of copy up
        self.keys = [right.keys[0]] if self.leaf else [right.keys.pop(0)]
        self.values = [left, right]
        self.leaf = False

        self._update_doubly_linked_list(left, right)

    def _update_doubly_linked_list(self, left: Self, right: Self) -> None:
        """Update link between cousins and siblings.

        :param left: left child
        :type left: Node
        :param right: right child
        :type right: Node
        """
        # cousin <- left  right -> cousin
        left.prev = self.prev
        right.next = self.next

        # cousin -> left  right <- cousin
        if self.prev:
            self.prev.next = left
        if self.next:
            self.next.prev = right

        # cousin left <-> right cousin
        left.next = right
        right.prev = left

    def show(self, level: int = 0) -> None:
        """Print the entries of the nodes recursively in preorder traversal.

        :param level: current tree level, defaults to 0
        :type level: int, optional
        """
        if self.leaf:
            seperate_symbol = ","
            start, end = "[", "]"
        else:
            seperate_symbol = ":"
            start, end = "(", ")"

        keys_padded = self.keys + ["__"] * (self.order - len(self.keys))
        keys_aligned = [f"{key:>2}" for key in keys_padded]
        keys_formatted = f"{start}{seperate_symbol.join(keys_aligned)}{end}"
        indentation = "    " * level
        print(f"{indentation}{keys_formatted}")

        if not self.leaf:
            for child in self.values:
                child.show(level + 1)
